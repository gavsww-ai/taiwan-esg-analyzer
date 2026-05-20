import argparse
import re
from pathlib import Path

import pandas as pd

from src.claim_extraction import (
    EXTERNAL_VALIDATION_PATTERN,
    PERCENT_PATTERN,
    STRONG_ACTION_PATTERN,
    YEAR_PATTERN,
    has_metric,
)


REQUIRED_COLUMNS = [
    "company",
    "category",
    "claim",
    "page",
    "confidence_score",
    "risk_level",
    "risk_reason",
]
OUTPUT_COLUMNS = REQUIRED_COLUMNS + ["analyst_note"]


def has_number_signal(claim: str) -> bool:
    return bool(re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", claim))


def has_action_signal(claim: str) -> bool:
    return bool(STRONG_ACTION_PATTERN.search(claim))


def score_review_claim(row: pd.Series) -> float:
    claim = str(row["claim"])
    score = float(row["confidence_score"])

    if has_metric(claim):
        score += 0.25
    if PERCENT_PATTERN.search(claim):
        score += 0.10
    if YEAR_PATTERN.search(claim):
        score += 0.20
    if has_number_signal(claim):
        score += 0.10
    if has_action_signal(claim):
        score += 0.20
    if row["risk_level"] == "Low":
        score += 0.15
    elif row["risk_level"] == "Medium":
        score += 0.08

    return round(score, 4)


def build_analyst_note(row: pd.Series) -> str:
    claim = str(row["claim"])
    strengths = []
    gaps = []

    if has_metric(claim):
        strengths.append("measurable KPI")
    else:
        gaps.append("metric")
    if YEAR_PATTERN.search(claim):
        strengths.append("target year")
    else:
        gaps.append("target year")
    if has_action_signal(claim):
        strengths.append("clear action language")
    if EXTERNAL_VALIDATION_PATTERN.search(claim):
        strengths.append("validation signal")
    else:
        gaps.append("external validation")

    if row["risk_level"] == "Low":
        return "Strong shortlist claim: " + ", ".join(strengths) + "."
    if strengths:
        if gaps:
            return "Useful claim with " + ", ".join(strengths) + f"; review missing {', '.join(gaps)}."
        return "Useful claim with " + ", ".join(strengths) + "; review source context."
    return "Potentially useful but less specific; review before citing."


def validate_input(df: pd.DataFrame) -> None:
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in filtered claims CSV: {sorted(missing)}")


def select_final_claims(
    df: pd.DataFrame,
    max_per_company_category: int = 5,
    max_total: int = 40,
) -> pd.DataFrame:
    validate_input(df)
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    ranked = df.copy()
    ranked["confidence_score"] = pd.to_numeric(ranked["confidence_score"], errors="coerce").fillna(0)
    ranked["_review_score"] = ranked.apply(score_review_claim, axis=1)
    ranked["analyst_note"] = ranked.apply(build_analyst_note, axis=1)

    ranked = ranked.sort_values(
        by=["company", "category", "_review_score", "confidence_score"],
        ascending=[True, True, False, False],
    )
    shortlist = ranked.groupby(["company", "category"], group_keys=False).head(max_per_company_category)

    # Keep the final cap balanced by taking the highest scoring claim from each
    # company/category group before filling remaining slots by score.
    group_keys = shortlist[["company", "category"]].drop_duplicates().itertuples(index=False, name=None)
    balanced_indexes = []
    for company, category in group_keys:
        group = shortlist[(shortlist["company"] == company) & (shortlist["category"] == category)]
        balanced_indexes.extend(group.head(1).index.tolist())

    balanced = shortlist.loc[balanced_indexes] if balanced_indexes else shortlist.head(0)
    if len(balanced) >= max_total:
        selected = balanced.sort_values(
            by=["_review_score", "confidence_score"],
            ascending=[False, False],
        ).head(max_total)
    else:
        remaining = shortlist.drop(index=balanced_indexes, errors="ignore")
        remaining = remaining.sort_values(
            by=["_review_score", "confidence_score"],
            ascending=[False, False],
        ).head(max_total - len(balanced))
        selected = pd.concat([balanced, remaining], ignore_index=False)
        selected = selected.sort_values(
            by=["_review_score", "confidence_score"],
            ascending=[False, False],
        )

    return selected[OUTPUT_COLUMNS].reset_index(drop=True)


def review_claims(
    input_path: str | Path = "data/extracted/filtered_claims.csv",
    output_path: str | Path = "data/extracted/final_claims.csv",
    max_per_company_category: int = 5,
    max_total: int = 40,
) -> pd.DataFrame:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Filtered claims file not found: {input_path}")

    df = pd.read_csv(source)
    final_claims = select_final_claims(
        df,
        max_per_company_category=max_per_company_category,
        max_total=max_total,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    final_claims.to_csv(destination, index=False)
    return final_claims


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a final analyst shortlist of ESG claims.")
    parser.add_argument("--input", default="data/extracted/filtered_claims.csv")
    parser.add_argument("--output", default="data/extracted/final_claims.csv")
    parser.add_argument("--max-per-company-category", type=int, default=5)
    parser.add_argument("--max-total", type=int, default=40)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    final_claims = review_claims(
        input_path=args.input,
        output_path=args.output,
        max_per_company_category=args.max_per_company_category,
        max_total=args.max_total,
    )
    print(f"Wrote {len(final_claims)} final claims to {args.output}")


if __name__ == "__main__":
    main()
