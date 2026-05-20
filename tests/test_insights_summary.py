import pandas as pd

from src.insights_summary import (
    build_insights_markdown,
    clean_text,
    priority_counts,
    strongest_supported_claims,
    top_review_priority_claims,
)


def make_row(
    company: str,
    category: str,
    flag: str,
    priority: str,
    claim: str,
    confidence: float = 0.8,
) -> dict:
    return {
        "company": company,
        "category": category,
        "claim": claim,
        "page": 10,
        "confidence_score": confidence,
        "risk_level": "Medium",
        "risk_reason": "Risk reason.",
        "analyst_note": "Analyst note.",
        "specificity_score": 3 if flag == "Strong" else 1,
        "measurability_score": 3 if flag == "Strong" else 1,
        "evidence_strength": 2 if flag == "Strong" else 0,
        "consistency_flag": flag,
        "review_priority": priority,
        "consistency_reason": "Consistency reason.",
    }


def test_build_insights_markdown_contains_required_sections():
    df = pd.DataFrame(
        [
            make_row(
                "TSMC",
                "emissions",
                "Weak",
                "High Review Priority",
                "TSMC will improve climate performance.",
            ),
            make_row(
                "ASEH",
                "renewable_energy",
                "Strong",
                "Low Review Priority",
                "ASEH will increase renewable energy by 3% by 2025 with RE100 reference.",
            ),
        ]
    )

    markdown = build_insights_markdown(df)

    assert "## Overall Project-Level Findings" in markdown
    assert "## Company-Level Findings" in markdown
    assert "## Category-Level Findings" in markdown
    assert "## Review-Priority Findings" in markdown
    assert "## Most Important Claims Needing Human Review" in markdown
    assert "## Strongest Supported Claims" in markdown
    assert "not investment advice" in markdown


def test_priority_counts_and_rankings():
    df = pd.DataFrame(
        [
            make_row("TSMC", "emissions", "Moderate", "Medium Review Priority", "Medium claim.", 0.9),
            make_row("TSMC", "emissions", "Weak", "High Review Priority", "Weak claim.", 0.7),
            make_row("ASEH", "governance", "Strong", "Low Review Priority", "Strong claim.", 0.8),
        ]
    )

    counts = priority_counts(df)
    top_review = top_review_priority_claims(df, limit=1)
    strongest = strongest_supported_claims(df, limit=1)

    assert counts["High Review Priority"] == 1
    assert top_review.iloc[0]["claim"] == "Weak claim."
    assert strongest.iloc[0]["claim"] == "Strong claim."


def test_clean_text_removes_common_pdf_encoding_artifacts():
    assert clean_text("target â€œrenewableâ€ claim") == 'target "renewable" claim'
