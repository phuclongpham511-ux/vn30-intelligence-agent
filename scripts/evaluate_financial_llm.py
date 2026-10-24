"""Separately invoked synthetic evaluation. Mock is always the default."""
import argparse
import json
from pathlib import Path
import sys

from src.schemas.financial_evaluation import LiveEvaluationConfig
from src.services.financial_evaluation import ACCEPTANCE_THRESHOLDS, evaluate, load_dataset
from src.services.financial_model_adapter import SyntheticEgressGate, SyntheticGatewayModel, prompt_digest


def run(argv=None):
    parser = argparse.ArgumentParser(description='Woofi synthetic-only LLM evaluation')
    parser.add_argument('--mode', choices=('mock', 'real'), default='mock')
    parser.add_argument('--config', help='Reviewed gateway/approval/budget JSON; no credentials')
    parser.add_argument('--enable-real', action='store_true')
    parser.add_argument('--authorize-synthetic-egress', action='store_true')
    parser.add_argument('--holdout', action='store_true')
    parser.add_argument('--release-holdout', action='store_true')
    parser.add_argument('--describe', action='store_true', help='Print approval hashes and thresholds, without inference')
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset('holdout' if args.holdout else 'development', release_holdout=args.release_holdout)
        if args.describe:
            print(json.dumps(dict(mode='readiness_only', dataset_sha256=dataset.sha256,
                prompt_sha256=prompt_digest(), split=dataset.split, thresholds=ACCEPTANCE_THRESHOLDS), indent=2))
            return 0
        if args.mode == 'real':
            if not (args.config and args.enable_real and args.authorize_synthetic_egress):
                raise ValueError('explicit_real_configuration_required')
            path = Path(args.config)
            if path.stat().st_size > 16384:
                raise ValueError('configuration_too_large')
            config = LiveEvaluationConfig.model_validate_json(path.read_bytes())
            model = SyntheticGatewayModel(config, SyntheticEgressGate(dataset),
                operator_enabled=args.enable_real, egress_authorized=args.authorize_synthetic_egress)
            report = evaluate(dataset, model=model, real=True,
                output_tokens=config.budget.per_request_output_tokens)
        else:
            if args.config or args.enable_real or args.authorize_synthetic_egress:
                raise ValueError('mock_does_not_consume_live_configuration')
            report = evaluate(dataset)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['acceptance_pass'] else 1
    except Exception:
        print('Evaluation refused or stopped; check approved synthetic dataset, consent and limits.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(run())
