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
    search_site_candidates,
    NAMED_SITES,
)
from portfolio_data import (
    load_portfolios,
    create_portfolio,
    update_portfolio,
    delete_portfolio,
    add_symbol_to_portfolio,
    increment_view_count,
)

RESULT_LIMIT_MIN, RESULT_LIMIT_MAX = 1, 999
DEFAULT_LIMIT = 50

st.set_page_config(
    page_title="High-Dividend Hunter",
    page_icon="📈",
    layout="wide",
)

# メニューバー用: デフォルトはランキングを取得
if "main_page" not in st.session_state:
    st.session_state["main_page"] = "ranking"

st.title("📈 High-Dividend Hunter")
col_m1, col_m2, col_m3, _ = st.columns([2, 2, 2, 10])
with col_m1:
    if st.button("ランキングを取得", use_container_width=True):
        st.session_state["main_page"] = "ranking"
        st.rerun()
with col_m2:
    if st.button("ポートフォリオを作成", use_container_width=True):
        st.session_state["main_page"] = "portfolio_create"
        st.rerun()
with col_m3:
    if st.button("My Portfolio", use_container_width=True):
        st.session_state["main_page"] = "my_portfolio"
        st.rerun()
st.divider()

if st.session_state["main_page"] == "portfolio_create":
    st.caption("リストの作成・編集・削除ができます。")
    portfolios = load_portfolios()
    with st.form("new_portfolio_form"):
        new_name = st.text_input("新規リスト名", placeholder="例: 高配当候補")
        if st.form_submit_button("作成"):
            if new_name and new_name.strip():
                create_portfolio(new_name.strip())
                st.success(f"「{new_name.strip()}」を作成しました。")
                st.rerun()
            else:
                st.error("リスト名を入力してください。")
    st.divider()
    for p in portfolios:
        pid, name, symbols = p.get("id"), p.get("name", ""), p.get("symbols") or []
        with st.expander(f"📁 {name}（{len(symbols)} 件）", expanded=False):
            edited = st.text_input("リスト名を編集", value=name, key=f"edit_{pid}")
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                if st.button("保存", key=f"save_{pid}"):
                    update_portfolio(pid, name=edited)
                    st.rerun()
            with col2:
                if st.button("削除", key=f"del_{pid}"):
                    delete_portfolio(pid)
                    st.rerun()
            if symbols:
                st.write("登録銘柄:", ", ".join(symbols))
            else:
                st.caption("銘柄はランキング取得ページのオプションから追加できます。")
    st.stop()

if st.session_state["main_page"] == "my_portfolio":
    if "view_portfolio_id" not in st.session_state:
        st.session_state["view_portfolio_id"] = None
    view_pid = st.session_state.get("view_portfolio_id")

    if view_pid:
        # 専用閲覧用ページ: 選択したポートフォリオの銘柄リスト（閲覧回数は遷移時1回のみ加算）
        if st.session_state.get("view_count_incremented_for") != view_pid:
            increment_view_count(view_pid)
            st.session_state["view_count_incremented_for"] = view_pid
        portfolios = load_portfolios()
        current = next((p for p in portfolios if p.get("id") == view_pid), None)
        if current:
            if st.button("← 一覧に戻る"):
                st.session_state["view_portfolio_id"] = None
                st.session_state.pop("view_count_incremented_for", None)
                st.rerun()
            st.subheader(current.get("name", ""))
            symbols = current.get("symbols") or []
            if symbols:
                for i, s in enumerate(symbols, 1):
                    st.write(f"{i}. {s}")
            else:
                st.caption("登録銘柄はありません。")
        else:
            st.session_state["view_portfolio_id"] = None
            st.rerun()
        st.stop()

    # My Portfolio トップ: 左上にメニュー（新規作成 / ポートフォリオを参照）
    st.caption("My Portfolio")
    col_mp1, col_mp2, _ = st.columns([2, 2, 8])
    with col_mp1:
        if st.button("新規作成", key="mp_new"):
            st.session_state["mp_open_new_dialog"] = True
            st.rerun()
    with col_mp2:
        st.write("**ポートフォリオを参照**（下の一覧から名前をクリック）")

    if st.session_state.get("mp_open_new_dialog"):
        with st.container():
            with st.form("my_portfolio_new_form"):
                new_name = st.text_input("ポートフォリオ名", key="mp_new_name", placeholder="任意の名前を入力")
                sub_col1, sub_col2, _ = st.columns([1, 1, 4])
                with sub_col1:
                    submit = st.form_submit_button("作成")
                with sub_col2:
                    cancel = st.form_submit_button("キャンセル")
                if submit and new_name and new_name.strip():
                    create_portfolio(new_name.strip())
                    st.session_state["mp_open_new_dialog"] = False
                    st.success(f"「{new_name.strip()}」を作成しました。")
                    st.rerun()
                if cancel:
                    st.session_state["mp_open_new_dialog"] = False
                    st.rerun()

    portfolios = load_portfolios()
    st.write("---")
    st.write("**作成済みポートフォリオ**")
    # ソート機能（修正3）: 作成日時 / 閲覧回数 / 銘柄数 の昇順・降順
    sort_option = st.selectbox(
        "並び替え",
        options=[
            "作成日時（新しい順）",
            "作成日時（古い順）",
            "閲覧回数（多い順）",
            "閲覧回数（少ない順）",
            "銘柄数（多い順）",
            "銘柄数（少ない順）",
        ],
        key="mp_sort",
    )
    if sort_option == "作成日時（新しい順）":
        portfolios = sorted(portfolios, key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_option == "作成日時（古い順）":
        portfolios = sorted(portfolios, key=lambda x: x.get("created_at", ""))
    elif sort_option == "閲覧回数（多い順）":
        portfolios = sorted(portfolios, key=lambda x: x.get("view_count", 0), reverse=True)
    elif sort_option == "閲覧回数（少ない順）":
        portfolios = sorted(portfolios, key=lambda x: x.get("view_count", 0))
    elif sort_option == "銘柄数（多い順）":
        portfolios = sorted(portfolios, key=lambda x: len(x.get("symbols") or []), reverse=True)
    else:
        portfolios = sorted(portfolios, key=lambda x: len(x.get("symbols") or []))
    for p in portfolios:
        name = p.get("name", "")
        pid = p.get("id", "")
        n = len(p.get("symbols") or [])
        if st.button(f"📁 {name}（{n} 件）", key=f"view_{pid}", use_container_width=True):
            st.session_state["view_portfolio_id"] = pid
            st.rerun()
    if not portfolios:
        st.caption("ポートフォリオがありません。「新規作成」で作成してください。")
    st.stop()

# ランキングを取得ページ
st.caption("Yahoo!ファイナンス 配当利回りランキングを取得し、テーブル表示・CSVダウンロードができます。")

input_mode = st.radio(
    "取得方法",
    options=["サイト名で選ぶ", "URLを直接入力"],
    horizontal=True,
)

target_url = None
if input_mode == "サイト名で選ぶ":
    search_query = st.text_input("キーワードで検索（候補を表示）", key="site_search_q", placeholder="例: 配当利回り ランキング")
    if st.button("検索", key="site_search_btn"):
        if search_query and search_query.strip():
            candidates = search_site_candidates(search_query.strip(), max_results=15)
            st.session_state["site_search_results"] = candidates
            st.rerun()
        else:
            st.warning("キーワードを入力してください。")
    search_results = st.session_state.get("site_search_results") or []
    combined = [(label, url) for label, url in search_results] + list(NAMED_SITES)
    if combined:
        idx = st.selectbox(
            "サイト候補（検索結果＋登録済み）",
            range(len(combined)),
            format_func=lambda i: combined[i][0],
            key="site_candidate_select",
        )
        target_url = combined[idx][1]
    else:
        selected = st.selectbox("サイト名", options=get_site_names(), index=0, key="site_fallback")
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
