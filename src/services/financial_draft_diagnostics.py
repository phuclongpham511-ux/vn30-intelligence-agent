"""Private, opt-in diffs for pinned synthetic development drafts only.

Expiry is enforced on startup/read/write. Use the explicit purge command after
a stopped session; no background service or scheduled task is installed here.
"""
from collections import Counter
import ctypes
from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
import uuid

from src.schemas.financial_assistant import ModelDraft
from src.services.financial_model_adapter import EvaluationStopped, prompt_digest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = 'woofi-synthetic-rejected-draft-v1'
NAME = re.compile(r'^rejected-[0-9a-f]{32}\.json$')
SENSITIVE = re.compile(r'(?i)(authorization\s*[:=]|bearer\s+|api[_-]?key|access[_-]?token|password|cookie\s*[:=]|gsk_[a-z0-9]|sk-[a-z0-9])')
ACL_SCRIPT = r'''
$ErrorActionPreference = 'Stop'
$target = $env:WOOFI_DIAGNOSTIC_PATH
$currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
if ($env:WOOFI_DIAGNOSTIC_CREATE -eq '1') {
    if (Test-Path -LiteralPath $target) { throw 'already_exists' }
    New-Item -ItemType Directory -Path $target -ErrorAction Stop | Out-Null
    $acl = Get-Acl -LiteralPath $target
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($sid in @($currentSid,$systemSid)) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $target -AclObject $acl
}
$item = Get-Item -LiteralPath $target -Force
if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'reparse_point' }
$acl = Get-Acl -LiteralPath $target
if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $currentSid.Value) { throw 'wrong_owner' }
if ($item.PSIsContainer -and -not $acl.AreAccessRulesProtected) { throw 'inherited_directory_acl' }
$seen = @()
foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
    if ($rule.IdentityReference.Value -notin @($currentSid.Value,$systemSid.Value)) { throw 'other_principal' }
    if ($rule.AccessControlType -ne 'Allow') { throw 'unexpected_deny' }
    if (($rule.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -ne [Security.AccessControl.FileSystemRights]::FullControl) { throw 'insufficient_rights' }
    $seen += $rule.IdentityReference.Value
}
if ($currentSid.Value -notin $seen -or $systemSid.Value -notin $seen) { throw 'missing_principal' }
Write-Output 'OK'
'''


def _windows_acl(path, *, create=False):
    shell = shutil.which('pwsh.exe') or shutil.which('pwsh')
    if not shell:
        shell = str(Path(os.environ.get('SYSTEMROOT','C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe')
    environment = {k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','LOCALAPPDATA','PROGRAMFILES'}}
    environment.update(WOOFI_DIAGNOSTIC_PATH=str(path), WOOFI_DIAGNOSTIC_CREATE='1' if create else '0')
    try:
        result = subprocess.run([shell,'-NoLogo','-NoProfile','-NonInteractive','-Command',ACL_SCRIPT],
            env=environment,capture_output=True,timeout=15)
    except (OSError,subprocess.TimeoutExpired):
        raise EvaluationStopped('diagnostic_storage_unsafe') from None
    if result.returncode != 0 or result.stdout.strip() != b'OK':
        raise EvaluationStopped('diagnostic_storage_unsafe')


def _safe_path(path):
    if not path.is_absolute() or str(path).startswith(('\\\\','//')):
        raise EvaluationStopped('diagnostic_storage_unsafe')
    for part in (path,*path.parents):
        try: info = part.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise EvaluationStopped('diagnostic_storage_unsafe')
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents or any(os.path.lexists(p/'.git') for p in (resolved,*resolved.parents)):
        raise EvaluationStopped('diagnostic_storage_unsafe')
    if os.name == 'nt':
        api = ctypes.WinDLL('kernel32',use_last_error=True)
        api.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
        if api.GetDriveTypeW(resolved.anchor) != 3:  # Fixed local disk only.
            raise EvaluationStopped('diagnostic_storage_unsafe')
    return resolved


def _private(path, *, directory):
    _safe_path(path)
    info = path.lstat()
    if not directory and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
        raise EvaluationStopped('diagnostic_storage_unsafe')
    if directory and not stat.S_ISDIR(info.st_mode):
        raise EvaluationStopped('diagnostic_storage_unsafe')
    if os.name == 'nt':
        _windows_acl(path)
    elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise EvaluationStopped('diagnostic_storage_unsafe')


class SyntheticDraftDiagnostics:
    MAX_ARTIFACTS = 32
    MAX_ARTIFACT_BYTES = 65536
    MAX_DIRECTORY_BYTES = 524288
    ARTIFACT_FIELDS = frozenset({'contract','artifact_id','classification','dataset_sha256',
        'prompt_sha256','case_id','created_at','expires_at','draft_sha256','schema_valid',
        'assessment','fact_ids','citations','answer_reference_fact_ids','answer_edits','missing_warning_bindings'})

    def __init__(self, dataset, directory, *, enabled=False, prompt_variant='default', retention_seconds=3600):
        from src.services.financial_evaluation import EvaluationDataset, DATASET_HASHES
        if (enabled is not True or type(dataset) is not EvaluationDataset or dataset.split != 'development' or
                dataset.sha256 != DATASET_HASHES['development']):
            raise EvaluationStopped('synthetic_diagnostics_explicit_pinned_dataset_required')
        dataset.cases()
        if type(retention_seconds) is not int or not 1 <= retention_seconds <= 3600:
            raise EvaluationStopped('diagnostic_retention_invalid')
        self.dataset = dataset
        self.prompt_variant = prompt_variant
        self.prompt_sha256 = prompt_digest(prompt_variant)
        self.retention_seconds = retention_seconds
        self.directory = _safe_path(Path(directory))
        self.artifacts_written = 0
        self.expired_removed = 0
        if not self.directory.exists():
            if not self.directory.parent.is_dir():
                raise EvaluationStopped('diagnostic_storage_unsafe')
            if os.name == 'nt': _windows_acl(self.directory,create=True)
            else: self.directory.mkdir(mode=0o700)
        self.preflight()

    def check_dataset(self, dataset, prompt_variant):
        from src.services.financial_evaluation import EvaluationDataset
        if (type(dataset) is not EvaluationDataset or dataset.split != 'development' or
                dataset.data != self.dataset.data or prompt_digest(prompt_variant) != self.prompt_sha256):
            raise EvaluationStopped('diagnostic_dataset_or_prompt_mismatch')
        self.preflight()

    def _owned(self, path):
        if path.parent != self.directory or not NAME.fullmatch(path.name):
            raise EvaluationStopped('diagnostic_foreign_file')
        _private(path,directory=False)
        with path.open('rb') as handle:
            raw = handle.read(self.MAX_ARTIFACT_BYTES+1)
        if len(raw) > self.MAX_ARTIFACT_BYTES or SENSITIVE.search(raw.decode('utf-8')):
            raise EvaluationStopped('diagnostic_storage_unsafe')
        try:
            item = json.loads(raw)
            if SENSITIVE.search(json.dumps(item,ensure_ascii=False)):
                raise ValueError
            if (set(item) != self.ARTIFACT_FIELDS or item['contract'] != CONTRACT or
                    item['artifact_id'] != path.stem[len('rejected-'):] or
                    item['classification'] != 'synthetic_non_sensitive' or
                    item['dataset_sha256'] != self.dataset.sha256 or item['prompt_sha256'] != self.prompt_sha256 or
                    item['case_id'] not in {c['id'] for c in self.dataset.cases()} or
                    type(item['created_at']) not in (int,float) or type(item['expires_at']) not in (int,float) or
                    not 0 < item['expires_at']-item['created_at'] <= 3600 or
                    item['created_at'] > time.time()+1):
                raise ValueError
        except Exception:
            raise EvaluationStopped('diagnostic_storage_unsafe') from None
        return item,len(raw)

    def preflight(self):
        _private(self.directory,directory=True)
        entries = []
        # Validate every entry before removing any expired artifact.
        for path in self.directory.iterdir():
            if len(entries)>=self.MAX_ARTIFACTS:
                raise EvaluationStopped('diagnostic_capacity_exhausted')
            item,size = self._owned(path)
            entries.append((path,item,size))
        live = []
        for path,item,size in entries:
            if item['expires_at'] <= time.time():
                if path.resolve().parent != self.directory: raise EvaluationStopped('diagnostic_storage_unsafe')
                path.unlink()  # One verified owned file, never recursive or wildcard deletion.
                self.expired_removed += 1
            else: live.append((path,size))
        if len(live)>self.MAX_ARTIFACTS or sum(size for _,size in live)>self.MAX_DIRECTORY_BYTES:
            raise EvaluationStopped('diagnostic_capacity_exhausted')
        return live

    def read_artifact(self, filename):
        if not NAME.fullmatch(filename): raise EvaluationStopped('diagnostic_foreign_file')
        self.preflight()
        path = self.directory/filename
        if not path.exists(): raise EvaluationStopped('diagnostic_expired_or_unavailable')
        item,_ = self._owned(path)
        if item['expires_at'] <= time.time(): raise EvaluationStopped('diagnostic_expired_or_unavailable')
        return item

    def record_rejection(self, case_id, raw):
        from src.services.financial_evaluation import prepare_case, assess_draft
        from src.services.financial_assistant import INTRO, render_fact
        live = self.preflight()
        case = next((c for c in self.dataset.cases() if c['id']==case_id),None)
        if case is None: raise EvaluationStopped('diagnostic_case_not_approved')
        if raw is not None and (not isinstance(raw,str) or len(raw.encode())>20000 or SENSITIVE.search(raw)):
            raise EvaluationStopped('diagnostic_sensitive_or_oversized_text')
        prepared = prepare_case(case)
        assessment = assess_draft(raw,prepared)
        if assessment['accepted']: return None
        try: draft = ModelDraft.model_validate_json(raw)
        except Exception: draft = None
        facts = prepared['facts']; catalog = {f.id:f for f in facts}
        expected_ids = [f.id for f in facts]
        expected_refs = sorted({ref for f in facts for ref in f.evidence_ids})
        binding_valid = draft is not None and len(draft.fact_ids)==len(catalog) and set(draft.fact_ids)==set(catalog)
        selected_ids = draft.fact_ids if binding_valid else expected_ids
        selected = [catalog[key] for key in selected_ids]
        expected_answer = INTRO+'\n'+'\n'.join(render_fact(f) for f in selected)
        edits = []
        if draft:
            left,right = expected_answer.splitlines(keepends=True),draft.answer.splitlines(keepends=True)
            edits = [dict(tag=tag,expected_start=i,expected_end=j,actual_lines=right[k:l])
                for tag,i,j,k,l in SequenceMatcher(None,left,right,autojunk=False).get_opcodes() if tag!='equal']
        def identities(expected,submitted):
            return dict(expected=expected,submitted=submitted,missing=sorted(set(expected)-set(submitted)),
                unexpected=sorted(set(submitted)-set(expected)),duplicates=sorted(k for k,v in Counter(submitted).items() if v>1),
                order_matches_expected=submitted==expected)
        warning='Còn thiếu bằng chứng; xem missing_information.'
        actual_lines=draft.answer.splitlines()[1:] if draft else []
        bindings=([dict(fact_id=f.id,line_index=i+1,warning_omitted=bool(f.missing_information) and
            (i>=len(actual_lines) or warning not in actual_lines[i])) for i,f in enumerate(selected) if f.missing_information]
            if binding_valid else [])
        now=time.time(); identifier=uuid.uuid4().hex
        item=dict(contract=CONTRACT,artifact_id=identifier,classification='synthetic_non_sensitive',
            dataset_sha256=self.dataset.sha256,prompt_sha256=self.prompt_sha256,case_id=case_id,
            created_at=now,expires_at=now+self.retention_seconds,draft_sha256=hashlib.sha256((raw or '').encode()).hexdigest(),
            schema_valid=draft is not None,assessment=assessment,
            fact_ids=identities(expected_ids,draft.fact_ids) if draft else None,
            citations=identities(expected_refs,draft.evidence_ids) if draft else None,
            answer_reference_fact_ids=selected_ids,answer_edits=edits,missing_warning_bindings=bindings)
        data=json.dumps(item,ensure_ascii=False,allow_nan=False).encode()
        # Check decoded/normalized content too: JSON unicode escapes must not
        # bypass the credential/header filter applied before parsing.
        if SENSITIVE.search(data.decode('utf-8')):
            raise EvaluationStopped('diagnostic_sensitive_or_oversized_text')
        if (len(data)>self.MAX_ARTIFACT_BYTES or len(live)>=self.MAX_ARTIFACTS or
                sum(size for _,size in live)+len(data)>self.MAX_DIRECTORY_BYTES):
            raise EvaluationStopped('diagnostic_capacity_exhausted')
        path=self.directory/('rejected-'+identifier+'.json')
        try:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
            with os.fdopen(fd,'wb') as handle:
                _private(path,directory=False)
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
        except Exception:
            raise EvaluationStopped('diagnostic_storage_write_failed') from None
        self.artifacts_written+=1
        return path.name
