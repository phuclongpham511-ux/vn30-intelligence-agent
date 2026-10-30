"""Trusted local terminal, mock only. Uses existing private opt-in environment.

python -m scripts.ask_financial_assistant --question "Kết quả tài chính FPT năm 2024"
No HTTP listener, history file, credentials or external model configuration.
"""
import argparse
import sys

from fastapi import HTTPException
from starlette.requests import Request

from src.services.financial_assistant import LocalFinancialAssistant


def run(argv=None):
    parser = argparse.ArgumentParser(description='Woofi local financial assistant (deterministic mock)')
    parser.add_argument('--question', help='Câu hỏi tiếng Việt; bỏ trống để dùng terminal tương tác')
    parser.add_argument('--capture-id', help='Chọn rõ một immutable capture ID khi có nhiều revisions')
    parser.add_argument('--json', action='store_true', help='In facts và evidence references có cấu trúc')
    args = parser.parse_args(argv)
    # A trusted terminal process has no remote socket identity. This local test
    # context still requires all existing private development opt-ins. Never use
    # it to authenticate a remote HTTP request or let question input supply it.
    request = Request(dict(type='http', scheme='http', method='POST', path='/', query_string=b'',
        headers=[(b'host', b'127.0.0.1')], client=('127.0.0.1', 0), server=('127.0.0.1', 0)))
    assistant = LocalFinancialAssistant(request)
    for _ in range(10):
        try:
            question = args.question if args.question is not None else input('Woofi (:quit để thoát)> ')
        except (EOFError, KeyboardInterrupt):
            return 0
        if question.strip() == ':quit':
            return 0
        payload = dict(question=question)
        if args.capture_id is not None:
            payload['capture_id'] = args.capture_id
        try:
            result = assistant.ask(payload)
        except HTTPException:
            print('Chưa được phép: cần cấu hình private development/loopback hiện có.', file=sys.stderr)
            return 2
        except Exception:
            # Terminal errors must not print source data, credentials or paths.
            print('Không thể đọc bằng chứng đã lưu một cách an toàn.', file=sys.stderr)
            return 2
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print(result.answer)
            if result.missing_information:
                print('Thông tin còn thiếu: ' + '; '.join(result.missing_information))
            print('\n'.join(result.limitations))
        if args.question is not None:
            return 0 if result.status in ('ANSWERED', 'SAFE_FALLBACK') else 1
    print('Đã đạt giới hạn phiên terminal; mở phiên mới khi cần.')
    return 0


if __name__ == '__main__':
    sys.exit(run())
