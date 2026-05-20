import pandas as pd

from src.consistency_analysis import analyze_claims, summary_statistics


def base_row(claim: str) -> dict:
    return {
        "company": "TSMC",
        "category": "emissions",
        "claim": claim,
        "page": 1,
        "confidence_score": 0.8,
        "risk_level": "Medium",
        "risk_reason": "Test risk reason.",
        "analyst_note": "Test analyst note.",
    }


def test_analyze_claims_flags_strong_claims():
    df = pd.DataFrame(
        [
            base_row(
                "TSMC will reduce Scope 1 emissions by 25% by 2030 under SBTi program criteria."
            )
        ]
    )

    result = analyze_claims(df)

    assert result.iloc[0]["specificity_score"] == 3
    assert result.iloc[0]["measurability_score"] == 3
    assert result.iloc[0]["evidence_strength"] >= 2
    assert result.iloc[0]["consistency_flag"] == "Strong"
    assert result.iloc[0]["review_priority"] == "Low Review Priority"


def test_analyze_claims_demotes_unvalidated_numeric_claims_to_moderate():
    df = pd.DataFrame(
        [
            base_row(
                "TSMC will reduce Scope 1 emissions by 25% by 2030 through a carbon reduction program."
            )
        ]
    )

    result = analyze_claims(df)

    assert result.iloc[0]["specificity_score"] == 3
    assert result.iloc[0]["consistency_flag"] == "Moderate"
    assert result.iloc[0]["review_priority"] == "Medium Review Priority"


def test_analyze_claims_flags_weak_aspirational_claims():
    df = pd.DataFrame([base_row("TSMC is committed to enhance and promote sustainable operations.")])

    result = analyze_claims(df)

    assert result.iloc[0]["specificity_score"] == 0
    assert result.iloc[0]["measurability_score"] == 0
    assert result.iloc[0]["consistency_flag"] == "Weak"
    assert result.iloc[0]["review_priority"] == "High Review Priority"


def test_summary_statistics_reports_percentages_and_category_averages():
    df = pd.DataFrame(
        [
            base_row("TSMC will reduce Scope 1 emissions by 25% by 2030 under SBTi program criteria."),
            base_row("TSMC is committed to enhance and promote sustainable operations."),
        ]
    )
    analyzed = analyze_claims(df)

    stats = summary_statistics(analyzed)

    assert stats["strong_pct"] == 50.0
    assert stats["weak_pct"] == 50.0
    assert list(stats["category_averages"]["category"]) == ["emissions"]
