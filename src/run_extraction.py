import argparse
from pathlib import Path

from src.claim_extraction import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract ESG claims from PDF reports.")
    parser.add_argument("--reports-dir", default="data/reports", help="Directory containing PDF reports.")
    parser.add_argument(
        "--template",
        default="data/claims_template.csv",
        help="CSV template of known ESG claims to compare against.",
    )
    parser.add_argument("--output-dir", default="data/extracted", help="Directory for JSON outputs.")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.65,
        help="Minimum confidence score for filtered_claims.csv.",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Print lightweight progress messages while parsing reports.",
    )
    parser.add_argument(
        "--include-unsupported",
        action="store_true",
        help="Also parse PDFs whose filenames are outside the TSMC/ASEH project scope.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of reports to parse in parallel. Use 1 for page-level progress.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        reports_dir=Path(args.reports_dir),
        template_path=Path(args.template),
        output_dir=Path(args.output_dir),
        min_confidence=args.min_confidence,
        progress_callback=(lambda message: print(message, flush=True)) if args.progress else None,
        include_unsupported_reports=args.include_unsupported,
        workers=args.workers,
    )
    print(
        f"Extracted {len(result.all_candidates)} ESG claim candidates; "
        f"kept {len(result.filtered_claims)} filtered claims in {args.output_dir}"
    )


if __name__ == "__main__":
    main()
