# October 16 runtime incident: bounded investigation and local checkpoint

INCIDENT_STATUS: PARTIAL. Supervisor fatal boundary confirmed; native census correction validated in isolation. Runtime remains stopped and unchanged. Per-service termination mechanics remain NOT_VERIFIED.

## Incident timeline

Primary times are UTC on 2026-10-16; ICT = UTC+07. Generation: f824274720474a5cb57d44c878b4c13e. Runtime: 844df8eb9bcff44670503cbfe4a5166b7f31e85f.

| UTC / ICT | Evidence | Qualification |
| --- | --- | --- |
| 10:29:23 / 17:29:23 | supervisor_started PID28340; three role_launch/ready receipts | Daily Use generation started normally; observers report no inherited job membership |
| 10:39:47 / 17:39:47 | Daily Use final native/HTTP acceptance | Saved healthy baseline |
| approximately 10:57 / 17:57 | Product research native/HTTP baseline | Roles ready, one collector, SQLite/FK PASS |
| 11:08:50.285436 / 18:08:50.285436 | manifest heartbeat | Last recorded daemon heartbeat; not proof of later health |
| 11:08:51.130200–11:35:51.975274 / 18:08:51–18:35:51 | Troubleshooter record168013 SleepTime/WakeTime; Kernel-Power42/107 records168000/168002 | Actual Sleep/Resume, not inferred |
| 11:35:50.500 / 18:35:50.500 | Kernel-General168003 old11:08:57.7949208 -> new11:35:50.500 | +1,612,705ms clock correction; raw record ordering matters |
| 11:36:02.873190–11:36:02.907727 / 18:36:02.873190–18:36:02.907727 | supervisor_stopped collector_inventory timeout15, then supervisor_exit expected=false | Recorded application exit decision; exact OS exit/code not captured |
| 11:41:19.626588 / 18:41:19.626588 | Backend role.log final modification, successful requests | Backend continued after Supervisor exit |
| 11:41:21.899138 / 18:41:21.899138 | Collector role.log final modification, normal ingestion cycles | Collector also continued; no forced acquisition by this task |
| 11:42:00.661328 / 18:42:00.661328 | User32 1074 record168017, StartMenuExperienceHost, power off | Separate OS shutdown request; no attribution to a particular physical user |
| from11:42:10.898248 / from18:42:10.898248 | Troubleshooter168302; Kernel-Power42 record168285 TargetState6/EffectiveState5 | Shutdown-to-hibernation, consistent with Fast Startup |
| 14:18:57.500 / 21:18:57.500 | Kernel-General168287 old11:42:17.0126096 -> new14:18:57.500; wake14:18:58.952180 | +9,400,487ms correction and subsequent wake |
| 14:27 / 21:27 | Price map preflight found departed identities | Cutover withheld before any lifecycle/pin action |
| 14:44:53 / 21:44:53 | This task's fresh native/Status/SQLite inspection | No canonical roles/listeners/DB or mutex holder; integrity/FK PASS |

LAST_HEALTHY_TIME: approximately10:57 UTC independently saved baseline; last manifest heartbeat11:08:50 UTC is separate.

SUPERVISOR_EXIT_TIME: recorded decision bounded11:36:02.873190–11:36:02.907727 UTC. Exact OS exit time/code NOT_VERIFIED. main() would return1 for this caught Conflict, but no process receipt proves the actual exit code.

SERVICE_EXIT_TIMELINE: Backend and Collector continued after the daemon ended. Frontend's last independent health is the initial baseline. All three current run directories lack exit.json and stop-*.json. Backend/Collector departures are bounded after their final logs and before14:27; Frontend after the healthy baseline and before14:27. OS power-off strongly explains subsequent user-session process disappearance, but no per-PID event proves exact ordering/signals/codes or successful graceful shutdown. Do not claim simultaneous exits caused by the probe timeout.

WINDOWS_POWER_EVENTS: two distinct transitions above; no unexpected-power-loss41 found in the exact provider/UTC window. WINDOWS_REBOOT_DETECTED: no cold kernel reboot established; boot identity remains2026-10-15T13:01:57.799754Z. This does not exclude hybrid shutdown. Microsoft documents Fast Startup logs off user sessions while retaining the kernel; the observed shutdown/state evidence is consistent with that mechanism. [Microsoft system power states](https://learn.microsoft.com/en-us/windows/win32/power/system-power-states).

CLOCK_CORRECTION_EVIDENCE: explicit Kernel-General payloads above. Initial FilterHashtable event queries unexpectedly included older records; final provider-qualified XPath and raw XML SystemTime establish the incident window. Record IDs preserve ordering across corrections.

## Cause and bounded correction

COLLECTOR_INVENTORY_TIMEOUT: deployed Windows.workers() starts PowerShell Get-CimInstance Win32_Process for each collector census, with a15-second subprocess deadline. Timeout becomes a labelled Conflict; run() saves blocked state/roles, logs supervisor_stopped and re-raises. This path neither signals nor terminates services. WMI-launched service roots are independent, so they can survive daemon exit.

CONFIRMED_ROOT_CAUSE: immediate Supervisor exit followed a fatal critical Collector probe timeout after real Sleep/Resume. Repeated PowerShell/CIM enumeration is a demonstrated availability boundary. Exact slow-CIM internals, probe start/PID and suspension contribution to its deadline are not established. No timer_gap/power_evidence event was recorded in this incident. Later OS power-off is a separate proven event.

UNVERIFIED_HYPOTHESES: particular CIM subsystem fault, exact per-service termination sequence or additional external termination. Security process-exit evidence requires elevated access and was unavailable. No correlated Python/pwsh/node application crash was found. Qualified11:00–11:45 WMI events concern NetworkAdapter/TPM queries, not Woofi Win32_Process; they are not attributed to this probe.

SUPERVISOR_ARCHITECTURE_FINDINGS: critical uncertainty must prohibit launch/signal; exiting is the existing intentional containment policy. An alive-but-latched-blocked daemon could retain observability, but needs reviewed Stop, pending-birth, epoch and retry semantics. It is not implemented here. A Windows Service is another future option with privileged installation, session/console/credential and migration risks; it still needs correct ownership census. No new supervisor/autostart installed.

MINIMAL_FIX: replace only Collector CIM enumeration with a5-second disposable base-Python native helper, reusing the sanitized listener bootstrap pattern. Fresh psutil instances qualify PID, creation time and executable; helper rows add CreationTime, checked against role members before mutex evaluation. Nonzero/timeout, invalid or empty JSON, missing metadata, duplicate PID, invalid type/count/time, denied access or changed identity fail closed. Only confirmed exits may be omitted. Process/response/allocation bounds apply; no command content or secrets enter diagnostics.

Review found psutil.name() derives its basename from exe(), which is empty for Windows Secure System. A real Toolhelp snapshot identified the name. A bounded TH32CS_SNAPPROCESS fallback qualifies empty names, rechecks creation time and accepts only ERROR_NO_MORE_FILES as successful completion. Missing/denied/invalid names, reused PID, invalid handle, iteration/close errors and count overflow remain unverified. There is no PID-specific exclusion. The helper deadline also bounds this native call. [Microsoft Toolhelp contract](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot), [psutil PID reuse documentation](https://psutil.readthedocs.io/stable/index.html).

Ingestion mutex, Restart Manager serialization, one-root/one-native-worker rules, role receipts/CWD, control locks, epochs, durable intent, pending-launch journals and recovery budget remain unchanged. Helpers import no application/provider and never open product DB. The patch removes CIM dependency; it does not certify all native calls after real sleep. Persistent critical failure still leaves the daemon blocked/exited with ownership retained, not healthy.

## Validation and recovery recommendation

REPRODUCTION: before source changes, three existing isolated boundary cases confirmed timeout propagation, daemon exit and preserved intent/manifest. New census coverage was initially26 RED. An early implementation passed244 focused tests. Review then added2 RED missing-metadata cases; strict handling exposed a real native compatibility failure (32 PASS/1 FAIL), diagnosed through Toolhelp and corrected rather than skipped or retried unchanged.

FOCUSED_TESTS: one244-PASS relevant regression run,75.65seconds, no failures/skips; after the review correction, all142 affected census/probe/inventory/exit-race cases PASS on final source,18.69seconds, no failures/skips. Explicitly split-run evidence, not a single final255-case run. Final new-file coverage42 cases includes native finite fake-module observation/timeout and deterministic API faults. Existing fixtures gained creation/executable metadata without weakened assertions. One existing Starlette/httpx warning. No full application/frontend suite, product ingestion/DB, forced Sleep or reboot.

CURRENT_RUNTIME_SHA: 844df8eb9bcff44670503cbfe4a5166b7f31e85f. Checkout HEAD and installed Supervisor match deployed source. origin/main remainsa866f3c2420f757e8822455eb110a49bd3f2daa1; Price map is preserved as the checkpoint's ancestor. No push/deployment.

CURRENT_PROCESS_STATE: zero canonical roles/listeners; all recorded PID/creation/executable identities departed. No DB/ingestion-mutex holder returned by native inspection. DESIRED_RUNNING: true, unchanged; manifest phaseblocked/control_phasestarting retained, no pending_launch. No manual journal reconciliation.

OWNERSHIP_SAFETY: PASS for observed stopped snapshot, not authority to launch. Config/status/intent/event hashes unchanged. Supported Start checks old identities/pending births and creates a fresh fenced epoch; any unknown owner must still block. Canonical -CheckOnly exited0: exact SHA, local credential reference recognized, existing DB/gate ready. Existing historical gate does not grant new execution authorization or prove restart stability.

DATABASE_INTEGRITY: PASS, raw mode=ro; integrityok/FK0. Schema/counts/Stock/Security/Story/Article/receipt identities and static Dividend/Technical provenance match14:27 snapshot. Articles5147, Stories4805, text receipts3553; Community threads167/observations3460; corporate records/documents30/25. Path unchanged; no claim about unavailable historical file-ID evidence. PilotOFF, FPTPAUSED; qualification/policy unchanged.

BACKUP: referenced20261016T103541050077Z/woofi.db still matches SHA2565af8820812410f571e695b0956b94dae3d39b4a7240680a86c11f4aae4fc44bb, integrity/FK PASS;4974articles versus live5147, consistent with later logged ingestion. Never restore it over newer data. No backup creation, DB write, WAL/SHM/lock deletion or cooldown reset here. Recovery needs a fresh consistent online backup.

RECOVERY_READINESS: PARTIAL/NOT_EXECUTED. Current844df8e reaches supported preflight and has no observed ownership/data blocker, but retains the known census failure boundary. Local fix needs separate review/integration and controlled recovery authorization; isolated tests are not production acceptance. No automatic Resume/Start or intent/journal edit.

PRICE_MAP_RELEASE_READINESS: a866f3c source tests/build preserved; actual new-feature production browser acceptance stillNOT_VERIFIED. Research/frontend work not repeated; staged release inactive.

NEXT_SAFE_ACTION: review local native-census checkpoint, then separately authorize one supported controlled recovery with fresh online backup, native ownership/port/mutex checks, exact release/build verification and Technical PilotOFF. Preserve newest DB/journals and fail closed on uncertainty. Qualify one Collector, health/source scheduling and bounded stability; Price map requires actual desktop/mobile production acceptance before completion. No autostart/unbounded retry.

LOCAL_CHECKPOINT: exact SHA is recorded in the external FINAL_REPORT.md, avoiding a self-referential commit identifier.

Evidence: C:\Users\PC\.codex\tmp\woofi-incident-20261016 contains current.json, preservation.json, power-exact-utc.json, wmi-exact-utc.json, application-exact-utc.json, canonical-checkonly.json, red/review logs, focused-final.xml and native-final.xml. Previous release evidence preserved.
