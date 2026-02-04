"""
High-Dividend Hunter: Yahoo!ファイナンス 配当利回りランキングのスクレイピングロジック
"""
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd


# デフォルトURL（設計書のURLと現行のYahoo!ファイナンスの両方に対応）
DEFAULT_URL = "https://finance.yahoo.co.jp/stocks/ranking/dividendYield?market=all"
FALLBACK_URL = "https://finance.yahoo.co.jp/ranking/dividendYield"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}


def _get_soup(url: str) -> BeautifulSoup:
    """指定URLにGETし、BeautifulSoupオブジェクトを返す。失敗時は例外を投げる。"""
    time.sleep(1)  # マナー: 必ず1秒以上間隔を空ける
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return BeautifulSoup(resp.text, "html.parser")


def _normalize_cell(text: str) -> str:
    """セルテキストの前後の空白・改行を整理する。"""
    if not text or not isinstance(text, str):
        return ""
    return " ".join(text.split()).strip()


def _find_ranking_table(soup: BeautifulSoup):
    """
    ランキング用のテーブルを探す。
    ヘッダーに「順位」または「配当利回り」を含むテーブルを優先する。
    """
    tables = soup.find_all("table")
    for table in tables:
        thead = table.find("thead")
        header_cells = thead.find_all("th") if thead else table.find_all("th")
        if not header_cells:
            first_row = table.find("tr")
            if first_row:
                header_cells = first_row.find_all(["th", "td"])
        header_texts = [_normalize_cell(th.get_text()) for th in header_cells]
        if any("順位" in h or "配当利回り" in h for h in header_texts):
            return table, header_texts
    return None, []


def _parse_table_rows(table, header_texts: list) -> list[dict]:
    """テーブルからデータ行をパースし、辞書のリストを返す。"""
    rows_data = []
    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")

    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        # ヘッダー行とデータ行の区別（先頭が「順位」の行はスキップ）
        cell_texts = [_normalize_cell(c.get_text()) for c in cells]
        if cell_texts and cell_texts[0] == "順位":
            continue
        # 列数がヘッダーと揃わない場合はスキップ
        n = min(len(header_texts), len(cell_texts))
        if n == 0:
            continue
        row_dict = {}
        for i in range(n):
            key = header_texts[i] or f"col_{i}"
            row_dict[key] = cell_texts[i]
        # 余った列は col_N で追加
        for i in range(n, len(cell_texts)):
            row_dict[f"col_{i}"] = cell_texts[i]
        rows_data.append(row_dict)
    return rows_data


def hunt_high_dividend(url: str | None = None) -> pd.DataFrame:
    """
    指定されたYahoo!ファイナンスの配当利回りランキングURLからデータを取得し、
    DataFrameを返す。

    Args:
        url: 取得先URL。Noneの場合はDEFAULT_URLを使用し、失敗時はFALLBACK_URLを試行。

    Returns:
        ランキングデータのDataFrame。取得失敗時は空のDataFrameを返す。
    """
    target_url = url or DEFAULT_URL
    urls_to_try = [target_url]
    if target_url == DEFAULT_URL:
        urls_to_try.append(FALLBACK_URL)

    for u in urls_to_try:
        try:
            soup = _get_soup(u)
            table, header_texts = _find_ranking_table(soup)
            if table is None or not header_texts:
                continue
            rows = _parse_table_rows(table, header_texts)
            if not rows:
                continue
            df = pd.DataFrame(rows)
            return df
        except requests.RequestException as e:
            # 次のURLを試すか、最後なら空のDataFrameを返す
            if u == urls_to_try[-1]:
                return pd.DataFrame()
            time.sleep(1)
            continue
        except Exception:
            if u == urls_to_try[-1]:
                return pd.DataFrame()
            time.sleep(1)
            continue

    return pd.DataFrame()
