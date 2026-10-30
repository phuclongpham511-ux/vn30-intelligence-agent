"""Separately invoked synthetic evaluation. Mock is always the default."""
import argparse
import json
from pathlib import Path
import sys

from src.schemas.financial_evaluation import LiveEvaluationConfig
from src.services.financial_evaluation import ACCEPTANCE_THRESHOLDS, evaluate, load_dataset
from src.services.financial_model_adapter import PROMPT_VARIANTS, SyntheticEgressGate, SyntheticGatewayModel, prompt_digest


def run(argv=None):
    parser = argparse.ArgumentParser(description='Woofi synthetic-only LLM evaluation')
    parser.add_argument('--mode', choices=('mock', 'real'), default='mock')
    parser.add_argument('--config', help='Reviewed gateway/approval/budget JSON; no credentials')
    parser.add_argument('--enable-real', action='store_true')
    parser.add_argument('--authorize-synthetic-egress', action='store_true')
    parser.add_argument('--request-interval-seconds', type=float, default=0,
        help='Optional spacing between real requests; recorded separately from model latency')
    parser.add_argument('--holdout', action='store_true')
    parser.add_argument('--release-holdout', action='store_true')
    parser.add_argument('--describe', action='store_true', help='Print approval hashes and thresholds, without inference')
    parser.add_argument('--prompt-variant', choices=PROMPT_VARIANTS, default='default')
    parser.add_argument('--enable-rejected-draft-diagnostics', action='store_true')
    parser.add_argument('--diagnostics-directory', type=Path)
    parser.add_argument('--diagnostic-retention-seconds', type=int, default=3600)
    parser.add_argument('--purge-expired-diagnostics', action='store_true')
    args = parser.parse_args(argv)
    try:
        diagnostics = None
        requested = (args.enable_rejected_draft_diagnostics or args.diagnostics_directory is not None or
            args.purge_expired_diagnostics or args.diagnostic_retention_seconds != 3600)
        if requested and (not args.enable_rejected_draft_diagnostics or args.diagnostics_directory is None or args.holdout or args.describe):
            raise ValueError('explicit_development_diagnostics_required')
        if args.purge_expired_diagnostics and (args.mode != 'mock' or args.config or args.enable_real or args.authorize_synthetic_egress):
            raise ValueError('purge_must_not_enable_inference')
        dataset = load_dataset('holdout' if args.holdout else 'development', release_holdout=args.release_holdout)
        if requested:
            from src.services.financial_draft_diagnostics import SyntheticDraftDiagnostics
            diagnostics = SyntheticDraftDiagnostics(dataset,args.diagnostics_directory,
                enabled=True,prompt_variant=args.prompt_variant,retention_seconds=args.diagnostic_retention_seconds)
        if args.purge_expired_diagnostics:
            print(json.dumps(dict(expired_artifacts_removed=diagnostics.expired_removed)))
            return 0
        if args.describe:
            print(json.dumps(dict(mode='readiness_only', dataset_sha256=dataset.sha256,
                prompt_sha256=prompt_digest(args.prompt_variant), split=dataset.split, thresholds=ACCEPTANCE_THRESHOLDS), indent=2))
            return 0
        if args.mode == 'real':
            if not (args.config and args.enable_real and args.authorize_synthetic_egress):
                raise ValueError('explicit_real_configuration_required')
            path = Path(args.config)
            if path.stat().st_size > 16384:
                raise ValueError('configuration_too_large')
            config = LiveEvaluationConfig.model_validate_json(path.read_bytes())
            model = SyntheticGatewayModel(config, SyntheticEgressGate(dataset),
                operator_enabled=args.enable_real, egress_authorized=args.authorize_synthetic_egress,
                prompt_variant=args.prompt_variant)
            report = evaluate(dataset, model=model, real=True,
                output_tokens=config.budget.per_request_output_tokens,
                request_interval_seconds=args.request_interval_seconds, prompt_variant=args.prompt_variant,
                diagnostics=diagnostics)
        else:
            if args.config or args.enable_real or args.authorize_synthetic_egress or args.request_interval_seconds:
                raise ValueError('mock_does_not_consume_live_configuration')
            report = evaluate(dataset, prompt_variant=args.prompt_variant, diagnostics=diagnostics)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['acceptance_pass'] else 1
    except Exception:
        print('Evaluation refused or stopped; check approved synthetic dataset, consent and limits.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(run())
