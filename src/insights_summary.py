import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "company",
    "category",
    "claim",
    "page",
    "confidence_score",
    "risk_level",
    "risk_reason",
    "analyst_note",
    "specificity_score",
    "measurability_score",
    "evidence_strength",
    "consistency_flag",
    "review_priority",
    "consistency_reason",
]

PRIORITY_ORDER = {
    "High Review Priority": 0,
    "Medium Review Priority": 1,
    "Low Review Priority": 2,
}
FLAG_ORDER = {
    "Weak": 0,
    "Moderate": 1,
    "Strong": 2,
}
TEXT_REPLACEMENTS = {
    "â€œ": '"',
    "â€": '"',
    "â€™": "'",
    "â€“": "-",
    "â€”": "-",
    "â€¢": "-",
    "�": "",
}


def validate_input(df: pd.DataFrame) -> None:
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in consistency analysis CSV: {sorted(missing)}")


def clean_text(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    for bad, good in TEXT_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return " ".join(text.split())


def priority_counts(df: pd.DataFrame) -> dict[str, int]:
    counts = df["review_priority"].value_counts().to_dict()
    return {
        "High Review Priority": int(counts.get("High Review Priority", 0)),
        "Medium Review Priority": int(counts.get("Medium Review Priority", 0)),
        "Low Review Priority": int(counts.get("Low Review Priority", 0)),
    }


def flag_counts(df: pd.DataFrame) -> dict[str, int]:
    counts = df["consistency_flag"].value_counts().to_dict()
    return {
        "Strong": int(counts.get("Strong", 0)),
        "Moderate": int(counts.get("Moderate", 0)),
        "Weak": int(counts.get("Weak", 0)),
    }


def top_review_priority_claims(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    ranked = df.copy()
    ranked["_priority_order"] = ranked["review_priority"].map(PRIORITY_ORDER).fillna(99)
    ranked["_flag_order"] = ranked["consistency_flag"].map(FLAG_ORDER).fillna(99)
    return (
        ranked.sort_values(
            by=["_priority_order", "_flag_order", "confidence_score"],
            ascending=[True, True, False],
        )
        .head(limit)
        .drop(columns=["_priority_order", "_flag_order"])
    )


def strongest_supported_claims(df: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    strong = df[df["consistency_flag"] == "Strong"].copy()
    if strong.empty:
        return strong.head(0)
    strong["_support_score"] = (
        strong["specificity_score"]
        + strong["measurability_score"]
        + strong["evidence_strength"]
        + strong["confidence_score"]
    )
    return (
        strong.sort_values(by=["_support_score", "confidence_score"], ascending=[False, False])
        .head(limit)
        .drop(columns=["_support_score"])
    )


def company_findings(df: pd.DataFrame, company: str) -> str:
    subset = df[df["company"] == company]
    if subset.empty:
        return f"- {company}: no claims in the current consistency analysis output."

    flags = flag_counts(subset)
    priorities = priority_counts(subset)
    dominant_categories = subset["category"].value_counts().head(2).index.tolist()
    category_text = ", ".join(dominant_categories) if dominant_categories else "no dominant category"
    return (
        f"- {company}: {len(subset)} claims reviewed. "
        f"Consistency mix is {flags['Strong']} Strong, {flags['Moderate']} Moderate, "
        f"{flags['Weak']} Weak. Review load is {priorities['High Review Priority']} High, "
        f"{priorities['Medium Review Priority']} Medium, {priorities['Low Review Priority']} Low priority. "
        f"Most represented categories: {category_text}."
    )


def category_findings(df: pd.DataFrame, category: str) -> str:
    subset = df[df["category"] == category]
    if subset.empty:
        return f"- {category}: no claims in the current output."

    flags = flag_counts(subset)
    avg_specificity = subset["specificity_score"].mean()
    avg_measurability = subset["measurability_score"].mean()
    avg_evidence = subset["evidence_strength"].mean()
    return (
        f"- {category}: {len(subset)} claims. "
        f"Consistency mix is {flags['Strong']} Strong, {flags['Moderate']} Moderate, "
        f"{flags['Weak']} Weak. Average scores: specificity {avg_specificity:.2f}, "
        f"measurability {avg_measurability:.2f}, evidence {avg_evidence:.2f}."
    )


def build_insights_markdown(df: pd.DataFrame) -> str:
    validate_input(df)
    total = len(df)
    flags = flag_counts(df)
    priorities = priority_counts(df)
    high_review = top_review_priority_claims(df, limit=5)
    strongest = strongest_supported_claims(df, limit=3)

    lines = [
        "# ESG Consistency Insights Summary",
        "",
        "## Overall Project-Level Findings",
        "",
        (
            f"The current consistency analysis reviews {total} final shortlisted ESG claims. "
            f"The stricter rule-based scoring identifies {flags['Strong']} Strong claims, "
            f"{flags['Moderate']} Moderate claims, and {flags['Weak']} Weak claims."
        ),
        "",
        (
            "The main analyst takeaway is that most claims still require human review. "
            "Many claims contain useful measurable detail, but fewer include the full set of "
            "KPI, year, quantitative value, and external validation needed for Strong support."
        ),
        "",
        "## Company-Level Findings",
        "",
        company_findings(df, "TSMC"),
        company_findings(df, "ASEH"),
        "",
        "## Category-Level Findings",
        "",
        category_findings(df, "emissions"),
        category_findings(df, "renewable_energy"),
        category_findings(df, "supply_chain"),
        category_findings(df, "governance"),
        "",
        "## Review-Priority Findings",
        "",
        f"- High Review Priority: {priorities['High Review Priority']} claims",
        f"- Medium Review Priority: {priorities['Medium Review Priority']} claims",
        f"- Low Review Priority: {priorities['Low Review Priority']} claims",
        "",
        "## Most Important Claims Needing Human Review",
        "",
    ]

    if high_review.empty:
        lines.append("No High Review Priority claims were found.")
    else:
        for _, row in high_review.iterrows():
            lines.extend(
                [
                    (
                        f"- {row['company']} | {row['category']} | page {row['page']}: "
                        f"{clean_text(row['claim'])}"
                    ),
                    f"  - Reason: {clean_text(row['consistency_reason'])}",
                ]
            )

    lines.extend(["", "## Strongest Supported Claims", ""])
    if strongest.empty:
        lines.append("No Strong claims were found under the current rules.")
    else:
        for _, row in strongest.iterrows():
            lines.extend(
                [
                    (
                        f"- {row['company']} | {row['category']} | page {row['page']}: "
                        f"{clean_text(row['claim'])}"
                    ),
                    f"  - Why strong: {clean_text(row['consistency_reason'])}",
                ]
            )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The method is regex-first and can miss claims in tables, charts, or unusual PDF layouts.",
            "- Evidence is currently limited to the source reports and extracted text.",
            "- The pipeline does not perform external validation against SBTi, CDP, filings, or assurance databases yet.",
            "- This is not an official ESG rating.",
            "- This is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def write_insights_summary(
    input_path: str | Path = "data/extracted/consistency_analysis.csv",
    output_path: str | Path = "output/insights_summary.md",
) -> str:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Consistency analysis file not found: {input_path}")

    df = pd.read_csv(source)
    markdown = build_insights_markdown(df)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")
    return markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate analyst insights from consistency analysis.")
    parser.add_argument("--input", default="data/extracted/consistency_analysis.csv")
    parser.add_argument("--output", default="output/insights_summary.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_insights_summary(args.input, args.output)
    print(f"Wrote insights summary to {args.output}")


if __name__ == "__main__":
    main()
