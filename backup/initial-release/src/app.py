"""
High-Dividend Hunter: Streamlit Web UI
"""
import streamlit as st
from main import hunt_high_dividend, DEFAULT_URL

st.set_page_config(
    page_title="High-Dividend Hunter",
    page_icon="📈",
    layout="wide",
)

st.title("📈 High-Dividend Hunter")
st.caption("Yahoo!ファイナンス 配当利回りランキングを取得し、テーブル表示・CSVダウンロードができます。")

url = st.text_input(
    "ランキングURL（未入力の場合はデフォルトを使用）",
    value="",
    placeholder=DEFAULT_URL,
)
target_url = url.strip() or None

if st.button("ランキングを取得", type="primary"):
    with st.spinner("取得中… (マナーで1秒以上待機しています)"):
        df = hunt_high_dividend(url=target_url)

    if df is not None and not df.empty:
        st.success(f"取得件数: {len(df)} 件")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # CSVダウンロード
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSVをダウンロード",
            data=csv,
            file_name="high_dividend_ranking.csv",
            mime="text/csv",
        )
    else:
        st.warning("データを取得できませんでした。URLを確認するか、しばらく経ってから再試行してください。")
