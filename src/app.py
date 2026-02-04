"""
High-Dividend Hunter: Streamlit Web UI
"""
import streamlit as st
from main import (
    hunt_high_dividend,
    DEFAULT_URL,
    get_site_names,
    get_url_by_site_name,
    apply_ranking_filters,
)

RESULT_LIMIT_MIN, RESULT_LIMIT_MAX = 1, 999
DEFAULT_LIMIT = 50

st.set_page_config(
    page_title="High-Dividend Hunter",
    page_icon="📈",
    layout="wide",
)

st.title("📈 High-Dividend Hunter")
st.caption("Yahoo!ファイナンス 配当利回りランキングを取得し、テーブル表示・CSVダウンロードができます。")

input_mode = st.radio(
    "取得方法",
    options=["サイト名で選ぶ", "URLを直接入力"],
    horizontal=True,
)

target_url = None
if input_mode == "サイト名で選ぶ":
    site_names = get_site_names()
    selected = st.selectbox(
        "サイト名",
        options=site_names,
        index=0,
        help="登録済みのサイトから選択すると、対応するURLで取得します。",
    )
    target_url = get_url_by_site_name(selected)
else:
    url = st.text_input(
        "ランキングURL（未入力の場合はデフォルトを使用）",
        value="",
        placeholder=DEFAULT_URL,
    )
    target_url = url.strip() or None

limit = st.number_input(
    "取得件数",
    min_value=RESULT_LIMIT_MIN,
    max_value=RESULT_LIMIT_MAX,
    value=DEFAULT_LIMIT,
    step=1,
    help=f"{RESULT_LIMIT_MIN}〜{RESULT_LIMIT_MAX}件の範囲で指定してください。",
)

if st.button("ランキングを取得", type="primary"):
    with st.spinner("取得中… (マナーで1秒以上待機しています)"):
        df = hunt_high_dividend(url=target_url, limit=limit)
    if df is not None and not df.empty:
        st.session_state["ranking_df"] = df
    else:
        st.warning("データを取得できませんでした。URLを確認するか、しばらく経ってから再試行してください。")

df = st.session_state.get("ranking_df")
if df is not None and not df.empty:
    st.success(f"表示件数: {len(df)} 件（条件により絞り込み可）")

    with st.expander("条件で絞り込み", expanded=False):
        yield_min = st.number_input("配当利回り 最小（%）", value=None, min_value=0.0, max_value=100.0, step=0.1, key="y_min", placeholder="指定なし")
        yield_max = st.number_input("配当利回り 最大（%）", value=None, min_value=0.0, max_value=100.0, step=0.1, key="y_max", placeholder="指定なし")
        col_settlement = None
        for c in df.columns:
            if "決算" in str(c) and "月" in str(c):
                col_settlement = c
                break
        settlement_months = None
        if col_settlement:
            options = sorted(df[col_settlement].astype(str).str.strip().dropna().unique().tolist())
            if options:
                selected = st.multiselect("決算年月", options=options, default=[], key="settlement")
                if selected:
                    settlement_months = selected
        if not col_settlement:
            st.caption("決算年月は取得データに含まれる場合に表示されます。")
        industry = sector = None
        has_benefit = None
        for c in df.columns:
            if "業界" in str(c):
                opts = sorted(df[c].astype(str).str.strip().dropna().unique().tolist())
                if opts:
                    industry = st.multiselect("業界", options=opts, key="industry")
                break
        for c in df.columns:
            if "分野" in str(c):
                opts = sorted(df[c].astype(str).str.strip().dropna().unique().tolist())
                if opts:
                    sector = st.multiselect("分野", options=opts, key="sector")
                break
        for c in df.columns:
            if "株主優待" in str(c) or ("優待" in str(c) and "配当" not in str(c)):
                has_benefit = st.selectbox("株主優待", options=["指定なし", "あり", "なし"], key="benefit")
                has_benefit = {"指定なし": None, "あり": True, "なし": False}[has_benefit]
                break

    display_df = apply_ranking_filters(
        df,
        yield_min=yield_min,
        yield_max=yield_max,
        settlement_months=settlement_months,
        industry=industry or None,
        sector=sector or None,
        has_shareholder_benefit=has_benefit,
    )
    st.caption(f"絞り込み後: {len(display_df)} 件")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="CSVをダウンロード",
        data=csv,
        file_name="high_dividend_ranking.csv",
        mime="text/csv",
    )
