#!/usr/bin/env python3
"""Command-line helper for the SAIR IGP24 Public API.

Live calls read the API key from an environment variable only. Submission is
dry-run by default and requires `--execute`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.verifiers.sair_api import (  # noqa: E402
    DEFAULT_API_KEY_ENV,
    SAIRAPIError,
    SAIRAPIVerifier,
    load_polynomial_lines,
)


def _write_json(payload: Any, output_json: str | Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_json:
        Path(output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(output_json).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _labels_from_args(args: argparse.Namespace) -> list[str] | None:
    labels: list[str] = []
    for label in args.label or []:
        labels.append(label)
    if args.labels:
        labels.extend(item.strip() for item in args.labels.split(",") if item.strip())
    return labels or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api_key_env", default=DEFAULT_API_KEY_ENV, help="Environment variable containing the SAIR key")
    parser.add_argument("--base_url", default="https://api.sair.foundation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    progress = subparsers.add_parser("progress", help="Read IGP24 label-progress data")
    progress.add_argument("--label", action="append", help="Repeatable exact label filter, e.g. 24T25000")
    progress.add_argument("--labels", help="Comma-separated exact label filters")
    progress.add_argument("--limit", type=int, default=5000)
    progress.add_argument("--cursor")
    progress.add_argument("--include_empty", action=argparse.BooleanOptionalAction, default=True)
    progress.add_argument("--output_json")

    submissions = subparsers.add_parser("list-submissions", help="List my SAIR submissions")
    submissions.add_argument("--limit", type=int, default=100)
    submissions.add_argument("--cursor")
    submissions.add_argument("--output_json")

    read_submission = subparsers.add_parser("get-submission", help="Read one submission status")
    read_submission.add_argument("submission_id")
    read_submission.add_argument("--output_json")

    download = subparsers.add_parser("download-submission", help="Download submitted polynomial lines")
    download.add_argument("submission_id")
    download.add_argument("--output_txt")

    submit = subparsers.add_parser("submit", help="Validate or submit coefficient lines")
    submit.add_argument("--coefficients_txt", required=True)
    submit.add_argument("--description")
    submit.add_argument("--execute", action="store_true", help="Actually POST to SAIR; default is dry-run validation")
    submit.add_argument("--output_json")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = SAIRAPIVerifier(api_key_env=args.api_key_env, base_url=args.base_url, dry_run=not getattr(args, "execute", False))

    try:
        if args.command == "progress":
            payload = client.get_label_progress(
                labels=_labels_from_args(args),
                include_empty=args.include_empty,
                limit=args.limit,
                cursor=args.cursor,
            )
            _write_json(payload, args.output_json)
        elif args.command == "list-submissions":
            _write_json(client.list_my_submissions(limit=args.limit, cursor=args.cursor), args.output_json)
        elif args.command == "get-submission":
            _write_json(client.get_submission(args.submission_id), args.output_json)
        elif args.command == "download-submission":
            text = client.download_submission(args.submission_id)
            if args.output_txt:
                Path(args.output_txt).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output_txt).write_text(text, encoding="utf-8")
            else:
                sys.stdout.write(text)
        elif args.command == "submit":
            polynomials = load_polynomial_lines(args.coefficients_txt)
            payload = client.submit_polynomials(
                polynomials,
                description=args.description,
                dry_run=not args.execute,
            )
            _write_json(payload, args.output_json)
        else:
            raise AssertionError(f"unhandled command: {args.command}")
    except SAIRAPIError as exc:
        retry = f" retry_after={exc.retry_after}" if exc.retry_after else ""
        code = f" code={exc.code}" if exc.code else ""
        print(f"SAIR API helper error:{code}{retry} {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
