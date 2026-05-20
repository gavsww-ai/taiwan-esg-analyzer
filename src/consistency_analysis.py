import argparse
import re
from pathlib import Path
from typing import Dict

import pandas as pd

from src.claim_extraction import (
    EXTERNAL_VALIDATION_PATTERN,
    GENERIC_MARKETING_PATTERN,
    PERCENT_PATTERN,
    REDUCTION_PATTERN,
    YEAR_PATTERN,
    has_metric,
)


INPUT_COLUMNS = [
    "company",
    "category",
    "claim",
    "page",
    "confidence_score",
    "risk_level",
    "risk_reason",
    "analyst_note",
]
ANALYSIS_COLUMNS = [
    "specificity_score",
    "measurability_score",
    "evidence_strength",
    "consistency_flag",
    "review_priority",
    "consistency_reason",
]
OUTPUT_COLUMNS = INPUT_COLUMNS + ANALYSIS_COLUMNS

NUMBER_PATTERN = re.compile(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b")
IMPLEMENTATION_PATTERN = re.compile(
    r"\b(?:program|plan|initiative|agreement|criteria|inventory|assessment|"
    r"audit|platform|task force|committee|supplier|implementation|roadmap)\b",
    re.IGNORECASE,
)
BROAD_LANGUAGE_PATTERN = re.compile(
    r"\b(?:committed|commitment|enhance|promote|strengthen|support|improve|"
    r"advance|drive|foster|encourage|aim(?:s)? to|seek(?:s)? to|continue to)\b",
    re.IGNORECASE,
)


def has_number(claim: str) -> bool:
    return bool(NUMBER_PATTERN.search(claim))


def has_percentage_or_reduction_amount(claim: str) -> bool:
    return bool(PERCENT_PATTERN.search(claim) or (REDUCTION_PATTERN.search(claim) and has_number(claim)))


def has_quantitative_value(claim: str) -> bool:
    return bool(has_metric(claim) or has_percentage_or_reduction_amount(claim))


def has_target_or_reporting_year(claim: str) -> bool:
    return bool(YEAR_PATTERN.search(claim))


def has_evidence_or_standard(claim: str) -> bool:
    return bool(EXTERNAL_VALIDATION_PATTERN.search(claim))


def has_implementation_detail(claim: str) -> bool:
    return bool(IMPLEMENTATION_PATTERN.search(claim))


def score_specificity(claim: str) -> int:
    score = 0
    if has_metric(claim):
        score += 1
    if has_target_or_reporting_year(claim):
        score += 1
    if has_quantitative_value(claim):
        score += 1
    return score


def score_measurability(claim: str) -> int:
    score = 0
    if has_number(claim):
        score += 1
    if has_metric(claim):
        score += 1
    if has_evidence_or_standard(claim):
        score += 1
    return score


def score_evidence_strength(claim: str) -> int:
    score = 0
    if has_evidence_or_standard(claim):
        score += 1
    if has_implementation_detail(claim):
        score += 1
    if has_quantitative_value(claim) and not (GENERIC_MARKETING_PATTERN.search(claim) or BROAD_LANGUAGE_PATTERN.search(claim)):
        score += 1
    return score


def classify_consistency(
    claim: str,
    specificity_score: int,
    measurability_score: int,
    evidence_strength: int,
) -> str:
    has_required_strong_signals = all(
        [
            has_metric(claim),
            has_target_or_reporting_year(claim),
            has_quantitative_value(claim),
            has_evidence_or_standard(claim),
        ]
    )
    if has_required_strong_signals and evidence_strength >= 2:
        return "Strong"

    missing_count = sum(
        [
            not has_metric(claim),
            not has_target_or_reporting_year(claim),
            not has_quantitative_value(claim),
            not has_evidence_or_standard(claim),
            not has_implementation_detail(claim),
        ]
    )
    broad_without_evidence = bool(BROAD_LANGUAGE_PATTERN.search(claim)) and not has_evidence_or_standard(claim)
    if (
        broad_without_evidence
        or not has_metric(claim)
        or evidence_strength == 0
        or missing_count >= 3
    ):
        return "Weak"

    if has_number(claim) or has_metric(claim) or has_target_or_reporting_year(claim):
        return "Moderate"
    return "Weak"


def assign_review_priority(consistency_flag: str) -> str:
    priorities = {
        "Weak": "High Review Priority",
        "Moderate": "Medium Review Priority",
        "Strong": "Low Review Priority",
    }
    return priorities.get(consistency_flag, "High Review Priority")


def build_consistency_reason(
    claim: str,
    specificity_score: int,
    measurability_score: int,
    evidence_strength: int,
) -> str:
    strengths = []
    gaps = []

    if has_metric(claim):
        strengths.append("measurable KPI")
    else:
        gaps.append("measurable KPI")
    if has_target_or_reporting_year(claim):
        strengths.append("target or reporting year")
    else:
        gaps.append("target or reporting year")
    if has_quantitative_value(claim):
        strengths.append("quantitative value")
    else:
        gaps.append("specific quantitative value")
    if has_evidence_or_standard(claim):
        strengths.append("standard or validation reference")
    else:
        gaps.append("standard or validation reference")
    if has_implementation_detail(claim):
        strengths.append("implementation detail")
    else:
        gaps.append("implementation detail")
    if BROAD_LANGUAGE_PATTERN.search(claim):
        gaps.append("broad aspirational wording")

    score_text = (
        f"specificity={specificity_score}, "
        f"measurability={measurability_score}, evidence={evidence_strength}"
    )
    if strengths and gaps:
        return f"{score_text}; has {', '.join(strengths)}; missing {', '.join(gaps)}."
    if strengths:
        return f"{score_text}; has {', '.join(strengths)}."
    return f"{score_text}; lacks measurable or verifiable detail."


def analyze_claims(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(INPUT_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in final claims CSV: {sorted(missing)}")

    analyzed = df.copy()
    specificity_scores = []
    measurability_scores = []
    evidence_scores = []
    flags = []
    priorities = []
    reasons = []

    for claim in analyzed["claim"].astype(str):
        specificity = score_specificity(claim)
        measurability = score_measurability(claim)
        evidence = score_evidence_strength(claim)
        flag = classify_consistency(claim, specificity, measurability, evidence)

        specificity_scores.append(specificity)
        measurability_scores.append(measurability)
        evidence_scores.append(evidence)
        flags.append(flag)
        priorities.append(assign_review_priority(flag))
        reasons.append(build_consistency_reason(claim, specificity, measurability, evidence))

    analyzed["specificity_score"] = specificity_scores
    analyzed["measurability_score"] = measurability_scores
    analyzed["evidence_strength"] = evidence_scores
    analyzed["consistency_flag"] = flags
    analyzed["review_priority"] = priorities
    analyzed["consistency_reason"] = reasons
    return analyzed[OUTPUT_COLUMNS]


def summary_statistics(df: pd.DataFrame) -> Dict[str, object]:
    total = len(df)
    if total == 0:
        return {
            "strong_pct": 0.0,
            "weak_pct": 0.0,
            "category_averages": pd.DataFrame(
                columns=[
                    "category",
                    "specificity_score",
                    "measurability_score",
                    "evidence_strength",
                ]
            ),
        }

    category_averages = (
        df.groupby("category", as_index=False)[
            ["specificity_score", "measurability_score", "evidence_strength"]
        ]
        .mean()
        .round(2)
    )
    return {
        "strong_pct": round((df["consistency_flag"].eq("Strong").mean()) * 100, 1),
        "weak_pct": round((df["consistency_flag"].eq("Weak").mean()) * 100, 1),
        "category_averages": category_averages,
    }


def run_consistency_analysis(
    input_path: str | Path = "data/extracted/final_claims.csv",
    output_path: str | Path = "data/extracted/consistency_analysis.csv",
) -> pd.DataFrame:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Final claims file not found: {input_path}")

    final_claims = pd.read_csv(source)
    analyzed = analyze_claims(final_claims)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    analyzed.to_csv(destination, index=False)
    return analyzed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze ESG claim consistency.")
    parser.add_argument("--input", default="data/extracted/final_claims.csv")
    parser.add_argument("--output", default="data/extracted/consistency_analysis.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyzed = run_consistency_analysis(args.input, args.output)
    stats = summary_statistics(analyzed)
    print(f"Wrote {len(analyzed)} consistency rows to {args.output}")
    print(f"Strong claims: {stats['strong_pct']}%")
    print(f"Weak claims: {stats['weak_pct']}%")
    print("Category-level consistency averages:")
    print(stats["category_averages"].to_string(index=False))


if __name__ == "__main__":
    main()
