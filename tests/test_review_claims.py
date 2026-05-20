import pandas as pd

from src.review_claims import OUTPUT_COLUMNS, select_final_claims


def make_claim(company: str, category: str, index: int, confidence: float = 0.7) -> dict:
    return {
        "company": company,
        "category": category,
        "claim": f"{company} will reduce emissions by {index}% by 2030 and validate progress.",
        "page": index,
        "confidence_score": confidence,
        "risk_level": "Low",
        "risk_reason": "Specific metric, target year, and evidence or validation are present.",
    }


def test_select_final_claims_caps_per_company_category_and_total():
    rows = []
    for company in ["TSMC", "ASEH"]:
        for category in ["emissions", "renewable_energy", "supply_chain", "governance"]:
            for index in range(1, 8):
                rows.append(make_claim(company, category, index, confidence=0.70 + index / 100))

    result = select_final_claims(pd.DataFrame(rows), max_per_company_category=5, max_total=40)

    assert len(result) == 40
    assert list(result.columns) == OUTPUT_COLUMNS
    counts = result.groupby(["company", "category"]).size()
    assert counts.max() <= 5
    assert result["analyst_note"].str.len().min() > 0


def test_select_final_claims_prefers_numbers_years_actions_and_confidence():
    df = pd.DataFrame(
        [
            {
                "company": "TSMC",
                "category": "emissions",
                "claim": "TSMC is committed to climate leadership.",
                "page": 1,
                "confidence_score": 0.95,
                "risk_level": "High",
                "risk_reason": "Vague or aspirational claim without a measurable KPI.",
            },
            {
                "company": "TSMC",
                "category": "emissions",
                "claim": "TSMC will reduce Scope 1 emissions by 25% by 2030 and validate progress.",
                "page": 2,
                "confidence_score": 0.80,
                "risk_level": "Low",
                "risk_reason": "Specific metric, target year, and evidence or validation are present.",
            },
        ]
    )

    result = select_final_claims(df, max_per_company_category=1, max_total=1)

    assert len(result) == 1
    assert result.iloc[0]["page"] == 2


def test_select_final_claims_preserves_group_balance_before_filling():
    rows = []
    for index in range(1, 8):
        rows.append(make_claim("TSMC", "emissions", index, confidence=0.90))
    rows.append(make_claim("ASEH", "governance", 1, confidence=0.70))

    result = select_final_claims(pd.DataFrame(rows), max_per_company_category=5, max_total=2)

    groups = set(zip(result["company"], result["category"]))
    assert ("TSMC", "emissions") in groups
    assert ("ASEH", "governance") in groups
