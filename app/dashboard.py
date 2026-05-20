from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.insights_summary import (
    priority_counts,
    strongest_supported_claims,
    top_review_priority_claims,
)


REQUIRED_COLUMNS = [
    "company",
    "category",
    "claim",
    "page",
    "confidence_score",
    "risk_level",
    "risk_reason",
    "analyst_note",
]
CONSISTENCY_COLUMNS = [
    "specificity_score",
    "measurability_score",
    "evidence_strength",
    "consistency_flag",
    "review_priority",
    "consistency_reason",
]

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "extracted" / "final_claims.csv"
CONSISTENCY_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "extracted" / "consistency_analysis.csv"
)

FLAG_COLORS = {
    "Strong": "green",
    "Moderate": "yellow",
    "Weak": "red",
    "High Review Priority": "red",
    "Medium Review Priority": "yellow",
    "Low Review Priority": "green",
    "Low": "green",
    "Medium": "yellow",
    "High": "red",
}
CHART_COLORS = {
    "Strong": "#3f7d66",
    "Moderate": "#c78a24",
    "Weak": "#b64b57",
    "Low": "#3f7d66",
    "Medium": "#c78a24",
    "High": "#b64b57",
    "Emissions": "#203a5f",
    "Governance": "#5f6f86",
    "Renewable Energy": "#3f7d66",
    "Supply Chain": "#7b6a54",
}
PRIORITY_ORDER = {
    "High Review Priority": 0,
    "Medium Review Priority": 1,
    "Low Review Priority": 2,
}
FLAG_ORDER = {"Weak": 0, "Moderate": 1, "Strong": 2}


st.set_page_config(page_title="Taiwan Semiconductor ESG Analyzer", layout="wide")


def load_claims(path: Path) -> pd.DataFrame:
    source = CONSISTENCY_PATH if CONSISTENCY_PATH.exists() else path
    columns = REQUIRED_COLUMNS + CONSISTENCY_COLUMNS
    if not source.exists():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(source)
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(0)
    df["page"] = pd.to_numeric(df["page"], errors="coerce").fillna(0).astype(int)
    for column in ["specificity_score", "measurability_score", "evidence_strength"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    return df[columns]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy-900: #102033;
            --navy-800: #172a45;
            --navy-700: #203a5f;
            --ink-900: #111827;
            --ink-700: #374151;
            --ink-500: #667085;
            --line: #d9e1ea;
            --soft-bg: #f3f6f9;
            --card: #ffffff;
            --green-bg: #e6f4ee;
            --green-text: #17644a;
            --green-line: #b7dfd0;
            --amber-bg: #fff4d6;
            --amber-text: #8a5a12;
            --amber-line: #f1d18a;
            --red-bg: #fbe6e8;
            --red-text: #9f2835;
            --red-line: #efb8bf;
        }
        .stApp {
            background: var(--soft-bg);
            color: var(--ink-900);
        }
        .block-container {
            max-width: 1240px;
            padding-top: 4.25rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            color: var(--navy-900);
            letter-spacing: 0;
        }
        h1 {
            font-size: 2.35rem;
            font-weight: 760;
            margin-bottom: 0.4rem;
        }
        h3 {
            font-size: 1.15rem;
            font-weight: 720;
            margin-top: 1.25rem;
        }
        p, label, .stMarkdown {
            color: var(--ink-700);
        }
        div[data-testid="stCaptionContainer"] p {
            color: var(--ink-500);
            font-size: 0.92rem;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 1rem;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--line);
            gap: 0.25rem;
        }
        div[data-testid="stTabs"] [data-baseweb="tab"] {
            color: var(--ink-500);
            font-weight: 650;
            padding: 0.75rem 0.9rem;
        }
        div[data-testid="stTabs"] [aria-selected="true"] {
            color: var(--navy-900);
        }
        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: var(--navy-700);
            height: 3px;
        }
        hr {
            border-color: var(--line);
            margin: 1.7rem 0 1.4rem;
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
            border: 1px solid var(--line);
            border-radius: 8px;
            min-height: 118px;
            padding: 18px 18px 16px;
            box-shadow: 0 8px 24px rgba(16, 32, 51, 0.06);
        }
        div[data-testid="stMetricLabel"] {
            color: var(--ink-500);
            font-size: 0.8rem;
            font-weight: 720;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        div[data-testid="stMetricValue"] {
            color: var(--navy-900);
            font-size: 2.05rem;
            font-weight: 760;
        }
        div[data-baseweb="tag"],
        span[data-baseweb="tag"] {
            background: #e8eef5 !important;
            border: 1px solid #d3dce8 !important;
            border-radius: 6px;
            color: var(--navy-900) !important;
            font-weight: 650;
        }
        div[data-baseweb="tag"] span,
        span[data-baseweb="tag"] span,
        div[data-baseweb="tag"] svg,
        span[data-baseweb="tag"] svg {
            color: var(--navy-900) !important;
            fill: var(--navy-900) !important;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #ffffff;
            border-color: var(--line);
            border-radius: 8px;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(16, 32, 51, 0.04);
            overflow: hidden;
        }
        .chart-frame {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px 18px 8px;
            box-shadow: 0 6px 18px rgba(16, 32, 51, 0.04);
        }
        .section-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 20px;
            min-height: 132px;
            box-shadow: 0 8px 24px rgba(16, 32, 51, 0.06);
        }
        .company-card {
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
            border: 1px solid var(--line);
            border-top: 4px solid var(--navy-700);
            border-radius: 8px;
            padding: 20px;
            min-height: 250px;
            box-shadow: 0 8px 24px rgba(16, 32, 51, 0.06);
        }
        .card-title {
            color: var(--navy-900);
            font-size: 1.18rem;
            font-weight: 760;
            margin-bottom: 4px;
        }
        .muted {
            color: var(--ink-500);
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            border-top: 1px solid #edf1f5;
            color: var(--ink-700);
            padding-top: 10px;
            margin-top: 10px;
        }
        .stat-row strong {
            color: var(--navy-900);
            font-size: 1.05rem;
        }
        .badge {
            border-radius: 999px;
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            line-height: 1;
            margin: 2px 4px 2px 0;
            padding: 6px 10px;
            white-space: nowrap;
        }
        .badge-green {
            background: var(--green-bg);
            color: var(--green-text);
            border: 1px solid var(--green-line);
        }
        .badge-yellow {
            background: var(--amber-bg);
            color: var(--amber-text);
            border: 1px solid var(--amber-line);
        }
        .badge-red {
            background: var(--red-bg);
            color: var(--red-text);
            border: 1px solid var(--red-line);
        }
        .pipeline {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 14px 0 20px;
        }
        .pipeline-step {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
            color: var(--navy-900);
            font-weight: 650;
            padding: 11px 14px;
            box-shadow: 0 4px 14px rgba(16, 32, 51, 0.04);
        }
        .pipeline-arrow {
            color: var(--ink-500);
            font-weight: 700;
        }
        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 3px 12px rgba(16, 32, 51, 0.03);
        }
        div[data-testid="stExpander"] summary p {
            color: var(--navy-900);
            font-weight: 650;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(label: str) -> str:
    color = FLAG_COLORS.get(str(label), "yellow")
    return f'<span class="badge badge-{color}">{label}</span>'


def category_label(value: str) -> str:
    return str(value).replace("_", " ").title()


def sorted_value_counts(df: pd.DataFrame, column: str, order: list[str] | None = None) -> pd.DataFrame:
    counts = df[column].fillna("").astype(str).value_counts().rename_axis(column).reset_index(name="claims")
    if order:
        counts["_order"] = counts[column].map({value: index for index, value in enumerate(order)}).fillna(99)
        counts = counts.sort_values(["_order", column]).drop(columns="_order")
    return counts


def count_chart(
    df: pd.DataFrame,
    column: str,
    title: str,
    order: list[str] | None = None,
) -> None:
    st.subheader(title)
    counts = sorted_value_counts(df, column, order)
    if counts.empty:
        st.info("No claims match the current filters.")
        return
    if column == "review_priority":
        counts["label"] = counts[column].str.replace(" Review Priority", "", regex=False)
    elif column == "category":
        counts["label"] = counts[column].map(category_label)
    else:
        counts["label"] = counts[column]
    counts["color_label"] = counts["label"]
    color_domain = list(CHART_COLORS)
    color_range = [CHART_COLORS[value] for value in color_domain]
    chart = (
        alt.Chart(counts)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("label:N", title=None, sort=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("claims:Q", title="Claims", axis=alt.Axis(grid=True, tickMinStep=1)),
            color=alt.Color(
                "color_label:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Segment"),
                alt.Tooltip("claims:Q", title="Claims"),
            ],
        )
        .properties(height=285)
        .configure_axis(
            labelColor="#667085",
            titleColor="#667085",
            gridColor="#e8edf3",
            domainColor="#d9e1ea",
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def kpi_cards(df: pd.DataFrame) -> None:
    cols = st.columns(5)
    cols[0].metric("Total Final Claims", len(df))
    cols[1].metric("Strong Claims", int(df["consistency_flag"].eq("Strong").sum()))
    cols[2].metric("Moderate Claims", int(df["consistency_flag"].eq("Moderate").sum()))
    cols[3].metric("Weak Claims", int(df["consistency_flag"].eq("Weak").sum()))
    cols[4].metric(
        "High Review Priority",
        int(df["review_priority"].eq("High Review Priority").sum()),
    )


def top_review_priority_category(company_df: pd.DataFrame) -> str:
    if company_df.empty:
        return "No claims"
    ranked = company_df.copy()
    ranked["_priority_order"] = ranked["review_priority"].map(PRIORITY_ORDER).fillna(99)
    category_counts = (
        ranked.groupby("category", as_index=False)
        .agg(priority_order=("_priority_order", "min"), claims=("claim", "count"))
        .sort_values(["priority_order", "claims", "category"], ascending=[True, False, True])
    )
    if category_counts.empty:
        return "No claims"
    return category_label(category_counts.iloc[0]["category"])


def company_card(df: pd.DataFrame, company: str) -> None:
    company_df = df[df["company"] == company]
    flag_counts = company_df["consistency_flag"].value_counts().to_dict()
    html = f"""
    <div class="company-card">
        <div class="card-title">{company}</div>
        <div class="muted">Analyst shortlist profile</div>
        <div class="stat-row"><span>Total claims</span><strong>{len(company_df)}</strong></div>
        <div class="stat-row"><span>{badge("Strong")}</span><strong>{int(flag_counts.get("Strong", 0))}</strong></div>
        <div class="stat-row"><span>{badge("Moderate")}</span><strong>{int(flag_counts.get("Moderate", 0))}</strong></div>
        <div class="stat-row"><span>{badge("Weak")}</span><strong>{int(flag_counts.get("Weak", 0))}</strong></div>
        <div class="stat-row"><span>Top review category</span><strong>{top_review_priority_category(company_df)}</strong></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def filter_claims(df: pd.DataFrame) -> pd.DataFrame:
    cols = st.columns([1, 1, 1, 1])
    companies = sorted(df["company"].dropna().astype(str).unique())
    categories = sorted(df["category"].dropna().astype(str).unique())
    flags = ["Strong", "Moderate", "Weak"]
    priority_labels = {
        "High": "High Review Priority",
        "Medium": "Medium Review Priority",
        "Low": "Low Review Priority",
    }

    selected_companies = cols[0].multiselect("Company", companies, default=companies)
    selected_categories = cols[1].multiselect(
        "Category",
        categories,
        default=categories,
        format_func=category_label,
    )
    selected_flags = cols[2].multiselect("Consistency", flags, default=flags)
    selected_priority_labels = cols[3].multiselect(
        "Review Priority",
        list(priority_labels),
        default=list(priority_labels),
    )
    selected_priorities = [priority_labels[label] for label in selected_priority_labels]
    search = st.text_input("Search claims, reasons, and analyst notes", placeholder="Search by keyword")

    filtered = df.copy()
    if selected_companies:
        filtered = filtered[filtered["company"].isin(selected_companies)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if selected_flags:
        filtered = filtered[filtered["consistency_flag"].isin(selected_flags)]
    if selected_priorities:
        filtered = filtered[filtered["review_priority"].isin(selected_priorities)]
    if search:
        pattern = search.lower()
        searchable = (
            filtered["claim"].astype(str)
            + " "
            + filtered["consistency_reason"].astype(str)
            + " "
            + filtered["risk_reason"].astype(str)
            + " "
            + filtered["analyst_note"].astype(str)
        ).str.lower()
        filtered = filtered[searchable.str.contains(pattern, regex=False)]
    return filtered


def claims_table(df: pd.DataFrame) -> None:
    table = df[
        [
            "company",
            "category",
            "page",
            "claim",
            "consistency_flag",
            "review_priority",
            "confidence_score",
        ]
    ].copy()
    table["category"] = table["category"].map(category_label)
    table = table.sort_values(["company", "category", "page"])
    table = table.rename(
        columns={
            "company": "Company",
            "category": "Category",
            "page": "Page",
            "claim": "Claim",
            "consistency_flag": "Consistency",
            "review_priority": "Review Priority",
            "confidence_score": "Confidence",
        }
    )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=430,
        column_config={
            "Claim": st.column_config.TextColumn("Claim", width="large"),
            "Review Priority": st.column_config.TextColumn("Review Priority", width="medium"),
            "Confidence": st.column_config.NumberColumn("Confidence", format="%.2f"),
        },
    )


def claim_detail_expanders(df: pd.DataFrame) -> None:
    ordered = df.copy()
    ordered["_priority_order"] = ordered["review_priority"].map(PRIORITY_ORDER).fillna(99)
    ordered["_flag_order"] = ordered["consistency_flag"].map(FLAG_ORDER).fillna(99)
    ordered = ordered.sort_values(["_priority_order", "_flag_order", "company", "category", "page"])

    for index, row in ordered.iterrows():
        label = f"{row['company']} | {category_label(row['category'])} | p. {row['page']} | {row['claim'][:90]}"
        with st.expander(label):
            st.markdown(
                f"{badge(row['consistency_flag'])} {badge(row['review_priority'])}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Claim**  \n{row['claim']}")
            st.markdown(f"**Page**  \n{row['page']}")
            st.markdown(f"**Consistency Reason**  \n{row['consistency_reason']}")
            st.markdown(f"**Risk Reason**  \n{row['risk_reason']}")
            st.markdown(f"**Analyst Note**  \n{row['analyst_note']}")


def priority_by_company_chart(df: pd.DataFrame) -> None:
    st.subheader("Review Priority by Company")
    priority_company = (
        df.groupby(["company", "review_priority"], as_index=False)
        .size()
        .rename(columns={"size": "claims"})
    )
    if priority_company.empty:
        st.info("No claims match the current filters.")
        return
    priority_company["priority_label"] = priority_company["review_priority"].str.replace(
        " Review Priority",
        "",
        regex=False,
    )
    chart = (
        alt.Chart(priority_company)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("company:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("claims:Q", title="Claims", stack="zero", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "priority_label:N",
                title="Priority",
                scale=alt.Scale(
                    domain=["High", "Medium", "Low"],
                    range=[CHART_COLORS["High"], CHART_COLORS["Medium"], CHART_COLORS["Low"]],
                ),
            ),
            tooltip=[
                alt.Tooltip("company:N", title="Company"),
                alt.Tooltip("priority_label:N", title="Priority"),
                alt.Tooltip("claims:Q", title="Claims"),
            ],
        )
        .properties(height=320)
        .configure_axis(
            labelColor="#667085",
            titleColor="#667085",
            gridColor="#e8edf3",
            domainColor="#d9e1ea",
        )
        .configure_legend(labelColor="#374151", titleColor="#102033", orient="top")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def methodology() -> None:
    st.markdown(
        """
        <div class="pipeline">
            <div class="pipeline-step">PDFs</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Extraction</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Filtering</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Final Review</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Consistency Analysis</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Insights</div><div class="pipeline-arrow">-></div>
            <div class="pipeline-step">Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        This dashboard presents the existing rule-based pipeline. It does not call external APIs,
        generate new ESG judgments, or alter the scoring logic. Claims are extracted from PDF text,
        filtered for specificity and duplicate risk, shortlisted for analyst review, then scored for
        consistency using transparent rules around specificity, measurability, and evidence strength.
        """
    )
    st.markdown(
        """
        **Portfolio constraints:** no agents, no LangChain, no vector database, no RAG, and no
        automated investment advice. The output is an analyst review aid for sustainable finance work.
        """
    )


inject_styles()
claims = load_claims(DATA_PATH)

st.title("Taiwan Semiconductor ESG Consistency Analyzer")
st.caption("Explainable ESG claim review for Taiwanese semiconductor sustainability reports.")

if claims.empty:
    st.warning(
        "No final claims found. Run `python -m src.review_claims` after generating filtered claims."
    )
    st.stop()

overview_tab, insights_tab, company_tab, consistency_tab, explorer_tab, methodology_tab = st.tabs(
    [
        "Overview",
        "Analyst Insights",
        "Company Comparison",
        "Consistency Analysis",
        "Claims Explorer",
        "Methodology",
    ]
)

with overview_tab:
    kpi_cards(claims)
    st.divider()
    chart_cols = st.columns(3)
    with chart_cols[0]:
        count_chart(claims, "consistency_flag", "Consistency Distribution", ["Strong", "Moderate", "Weak"])
    with chart_cols[1]:
        count_chart(
            claims,
            "review_priority",
            "Review Priority Distribution",
            ["High Review Priority", "Medium Review Priority", "Low Review Priority"],
        )
    with chart_cols[2]:
        count_chart(claims, "category", "Claims by Category")

    st.subheader("Review Snapshot")
    snapshot_cols = st.columns(2)
    with snapshot_cols[0]:
        st.markdown(
            f"""
            <div class="section-card">
                <div class="card-title">Portfolio Readiness</div>
                <div class="muted">The dashboard summarizes a 40-claim analyst shortlist with explainable rule-based scoring.</div>
                <div style="margin-top:12px;">{badge("Strong")} {badge("Moderate")} {badge("Weak")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with snapshot_cols[1]:
        st.markdown(
            f"""
            <div class="section-card">
                <div class="card-title">Review Load</div>
                <div class="muted">Priority badges separate high-touch analyst review from better-supported claims.</div>
                <div style="margin-top:12px;">{badge("High Review Priority")} {badge("Medium Review Priority")} {badge("Low Review Priority")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with insights_tab:
    kpi_cards(claims)
    priorities = priority_counts(claims)
    st.markdown(
        f"""
        {badge("High Review Priority")} {priorities["High Review Priority"]} claims need the closest analyst review.
        {badge("Medium Review Priority")} {priorities["Medium Review Priority"]} claims have partial support.
        {badge("Low Review Priority")} {priorities["Low Review Priority"]} claims are strongest under the current rules.
        """,
        unsafe_allow_html=True,
    )

    insight_cols = st.columns(2)
    with insight_cols[0]:
        st.subheader("Top High Review Priority Claims")
        top_review = top_review_priority_claims(claims, limit=5)
        st.dataframe(
            top_review[
                ["company", "category", "page", "claim", "review_priority", "consistency_reason"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    with insight_cols[1]:
        st.subheader("Strongest Supported Claims")
        strongest = strongest_supported_claims(claims, limit=5)
        if strongest.empty:
            st.info("No Strong claims found under the current rules.")
        else:
            st.dataframe(
                strongest[["company", "category", "page", "claim", "consistency_reason"]],
                use_container_width=True,
                hide_index=True,
            )

with company_tab:
    card_cols = st.columns(2)
    with card_cols[0]:
        company_card(claims, "TSMC")
    with card_cols[1]:
        company_card(claims, "ASEH")
    st.divider()
    priority_by_company_chart(claims)
    st.subheader("Company x Category Matrix")
    st.dataframe(pd.crosstab(claims["company"], claims["category"]), use_container_width=True)

with consistency_tab:
    kpi_cards(claims)
    st.divider()
    chart_cols = st.columns(2)
    with chart_cols[0]:
        count_chart(claims, "consistency_flag", "Consistency Distribution", ["Strong", "Moderate", "Weak"])
    with chart_cols[1]:
        count_chart(
            claims,
            "review_priority",
            "Review Priority Distribution",
            ["High Review Priority", "Medium Review Priority", "Low Review Priority"],
        )

    st.subheader("Category-Level Scores")
    st.dataframe(
        claims.groupby("category", as_index=False)
        .agg(
            claims=("claim", "count"),
            specificity_score=("specificity_score", "mean"),
            measurability_score=("measurability_score", "mean"),
            evidence_strength=("evidence_strength", "mean"),
        )
        .round(2)
        .sort_values("category"),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Consistency Review Table")
    review_table = claims.copy()
    review_table["_priority_order"] = review_table["review_priority"].map(PRIORITY_ORDER).fillna(99)
    st.dataframe(
        review_table.sort_values(["_priority_order", "company", "category", "page"])[
            [
                "company",
                "category",
                "page",
                "claim",
                "consistency_flag",
                "review_priority",
                "specificity_score",
                "measurability_score",
                "evidence_strength",
                "consistency_reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with explorer_tab:
    filtered_claims = filter_claims(claims)
    st.caption(f"{len(filtered_claims)} of {len(claims)} claims match the current filters.")
    claims_table(filtered_claims)
    st.subheader("Claim Detail")
    claim_detail_expanders(filtered_claims)

with methodology_tab:
    methodology()
