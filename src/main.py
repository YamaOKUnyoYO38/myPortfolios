"""
High-Dividend Hunter: Yahoo!ファイナンス 配当利回りランキングのスクレイピングロジック
"""
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd


# デフォルトURL（設計書のURLと現行のYahoo!ファイナンスの両方に対応）
DEFAULT_URL = "https://finance.yahoo.co.jp/stocks/ranking/dividendYield?market=all"
FALLBACK_URL = "https://finance.yahoo.co.jp/ranking/dividendYield"

# サイト名 → URL の登録リスト（サイト名でランキング取得用）
NAMED_SITES: list[tuple[str, str]] = [
    ("Yahoo!ファイナンス 配当利回り（会社予想）", DEFAULT_URL),
    ("Yahoo!ファイナンス 配当利回り（旧URL）", FALLBACK_URL),
    ("Yahoo!ファイナンス 株主優待配当利回り（2月）", "https://finance.yahoo.co.jp/stocks/incentive/dividendYield-ranking/month_2"),
    ("Yahoo!ファイナンス 株主優待配当利回り（3月）", "https://finance.yahoo.co.jp/stocks/incentive/dividendYield-ranking/month_3"),
    ("Yahoo!ファイナンス 優良高配当株", "https://finance.yahoo.co.jp/stocks/screening/highdividend"),
]


def get_site_names() -> list[str]:
    """登録済みサイト名のリストを返す。"""
    return [name for name, _ in NAMED_SITES]


def get_url_by_site_name(site_name: str) -> str | None:
    """サイト名に対応するURLを返す。見つからなければ None。"""
    for name, url in NAMED_SITES:
        if name == site_name:
            return url
    return None


def search_site_candidates(query: str, max_results: int = 20, include_english: bool = True) -> list[tuple[str, str]]:
    """
    入力キーワードでWWWを網羅的に検索し、(タイトル, URL) の候補を返す。
    英語サイト・文献も含める場合は複数クエリで検索して結果を統合する。
    """
    if not query or not query.strip():
        return []
    q = query.strip()
    seen_urls: set[str] = set()
    out: list[tuple[str, str]] = []

    def _run_search(search_term: str, n: int) -> None:
        nonlocal out, seen_urls
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(search_term, max_results=n))
            for r in results:
                href = (r.get("href") or "").strip()
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)
                title = (r.get("title") or "").strip() or href
                out.append((title, href))
        except Exception:
            pass
        time.sleep(0.5)

    # 1) 元のキーワードで検索（日本語・多言語）
    _run_search(q, max_results)

    # 2) 英語サイト・文献を含める: 英語向けクエリを追加
    if include_english and q:
        time.sleep(1)
        en_queries = [
            f"{q} dividend yield ranking",
            f"{q} high dividend stocks",
            f"dividend yield {q}",
        ]
        per = max(5, max_results // len(en_queries))
        for eq in en_queries:
            _run_search(eq, per)
            time.sleep(0.5)

    return out


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
        # 銘柄コード: 先頭セル内の quote/XXXX リンクから取得（ポートフォリオ追加用）
        symbol = ""
        if cells:
            a = cells[0].find("a", href=True)
            if a and "quote/" in a["href"]:
                symbol = a["href"].rstrip("/").split("quote/")[-1].split("?")[0] or ""
        row_dict["symbol"] = symbol
        rows_data.append(row_dict)
    return rows_data


def _fetch_one_page(url: str) -> pd.DataFrame | tuple[list[dict], list[str]] | None:
    """1ページ分を取得。成功時は (rows, header_texts)、テーブルなし時は None。"""
    try:
        soup = _get_soup(url)
        table, header_texts = _find_ranking_table(soup)
        if table is None or not header_texts:
            return None
        rows = _parse_table_rows(table, header_texts)
        if not rows:
            return None
        return rows, header_texts
    except requests.RequestException:
        return None
    except Exception:
        return None


def _url_append_page(base_url: str, page: int) -> str:
    """URL に page パラメータを付与（既存クエリには & で追加）。"""
    if "?" in base_url:
        return f"{base_url}&page={page}"
    return f"{base_url}?page={page}"


def hunt_high_dividend(url: str | None = None, limit: int | None = None) -> pd.DataFrame:
    """
    指定されたYahoo!ファイナンスの配当利回りランキングURLからデータを取得し、
    DataFrameを返す。

    Args:
        url: 取得先URL。Noneの場合はDEFAULT_URLを使用し、失敗時はFALLBACK_URLを試行。
        limit: 取得件数（1〜9999）。None の場合は1ページ分（最大50件程度）のみ取得。

    Returns:
        ランキングデータのDataFrame。取得失敗時は空のDataFrameを返す。
    """
    if limit is not None and (limit < 1 or limit > 9999):
        return pd.DataFrame()

    target_url = url or DEFAULT_URL
    urls_to_try = [target_url]
    if target_url == DEFAULT_URL:
        urls_to_try.append(FALLBACK_URL)

    all_rows: list[dict] = []
    header_texts: list[str] = []
    max_rows = limit if limit is not None else 50
    page = 1

    for base_url in urls_to_try:
        all_rows = []
        header_texts = []
        page = 1
        while len(all_rows) < max_rows:
            page_url = _url_append_page(base_url, page) if page > 1 else base_url
            result = _fetch_one_page(page_url)
            if result is None:
                break
            rows, header_texts = result
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < 50:
                break
            if limit is not None and len(all_rows) >= limit:
                break
            page += 1
        if all_rows and header_texts:
            df = pd.DataFrame(all_rows)
            if limit is not None:
                df = df.head(limit)
            return df
        time.sleep(1)

    return pd.DataFrame()


def _parse_yield_value(s: str) -> float | None:
    """配当利回りセル（例: '+6.72%'）を数値に変換。失敗時は None。"""
    if not s or not isinstance(s, str):
        return None
    s = s.replace("+", "").replace("%", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# 市場名らしいパターン（東証PRM, 東証STD, 名証, マザーズ 等）
_MARKET_PATTERN = re.compile(
    r"(東証(?:PRM|STD|グロース)?|名証(?:MN)?|マザーズ|札証|福証|JQS|東証)"
)


def _extract_market_from_name_cell(s: str) -> str:
    """名称・コード・市場セルから市場部分を返す。末尾トークンまたは既知パターンで抽出。"""
    if not s or not isinstance(s, str):
        return ""
    s = s.strip()
    # 1) 末尾のトークン（スペース区切り）
    parts = s.split()
    if parts:
        last = parts[-1].strip()
        if last and (last.startswith("東証") or last.startswith("名証") or "証" in last or last in ("マザーズ", "JQS")):
            return last
    # 2) 既知の市場パターンを文中から検索
    m = _MARKET_PATTERN.search(s)
    if m:
        return m.group(1)
    return parts[-1].strip() if parts else ""


def get_unique_markets(df: pd.DataFrame) -> list[str]:
    """DataFrame の名称・コード・市場列（または市場を含む列）から市場の一覧を返す。"""
    cand_columns = []
    for c in df.columns:
        col = str(c)
        if "名称" in col and "コード" in col and "市場" in col:
            cand_columns.insert(0, c)  # 優先
        elif "市場" in col or "名称" in col:
            cand_columns.append(c)
    for c in cand_columns:
        extracted = df[c].astype(str).map(_extract_market_from_name_cell)
        markets = extracted.replace("", pd.NA).dropna().unique().tolist()
        markets = [x for x in markets if x and len(x) <= 20]
        if markets:
            return sorted(markets)
    return []


def apply_ranking_filters(
    df: pd.DataFrame,
    yield_min: float | None = None,
    yield_max: float | None = None,
    settlement_months: list[str] | None = None,
    industry: list[str] | None = None,
    sector: list[str] | None = None,
    has_shareholder_benefit: bool | None = None,
    markets: list[str] | None = None,
) -> pd.DataFrame:
    """
    取得済みランキング DataFrame に条件をかけて絞り込む。

    Args:
        df: ランキングデータ
        yield_min / yield_max: 配当利回り（%）の範囲。None は制限なし。
        settlement_months: 決算年月で絞り込み。None は制限なし。
        industry / sector / has_shareholder_benefit: 列が存在する場合に適用。
        markets: 市場で絞り込み（例: ['東証PRM', '東証STD']）。None は制限なし（上場銘柄すべて）。
    """
    if df.empty:
        return df
    out = df.copy()

    # 配当利回り
    col_yield = None
    for c in out.columns:
        if "配当利回り" in str(c):
            col_yield = c
            break
    if col_yield:
        out["_parsed_yield"] = out[col_yield].astype(str).map(_parse_yield_value)
        out = out.dropna(subset=["_parsed_yield"])
        if yield_min is not None:
            out = out[out["_parsed_yield"] >= yield_min]
        if yield_max is not None:
            out = out[out["_parsed_yield"] <= yield_max]
        out = out.drop(columns=["_parsed_yield"])

    # 決算年月
    col_settlement = None
    for c in out.columns:
        if "決算" in str(c) and "月" in str(c):
            col_settlement = c
            break
    if col_settlement and settlement_months:
        out = out[out[col_settlement].astype(str).str.strip().isin(settlement_months)]

    # 業界（列がある場合のみ）
    for c in out.columns:
        if "業界" in str(c) and industry:
            out = out[out[c].astype(str).str.strip().isin(industry)]
            break

    # 分野（列がある場合のみ）
    for c in out.columns:
        if "分野" in str(c) and sector:
            out = out[out[c].astype(str).str.strip().isin(sector)]
            break

    # 株主優待（列がある場合のみ）
    for c in out.columns:
        if "株主優待" in str(c) or "優待" in str(c):
            if has_shareholder_benefit is True:
                out = out[out[c].astype(str).str.strip().str.lower().isin(("あり", "1", "true", "yes"))]
            elif has_shareholder_benefit is False:
                out = out[~out[c].astype(str).str.strip().str.lower().isin(("あり", "1", "true", "yes"))]
            break

    # 市場（各市場ごとの全銘柄: 指定した市場のみ表示）
    col_name_market = None
    for c in out.columns:
        if "名称" in str(c) and "コード" in str(c) and "市場" in str(c):
            col_name_market = c
            break
    if col_name_market and markets:
        out["_market"] = out[col_name_market].astype(str).map(_extract_market_from_name_cell)
        out = out[out["_market"].isin(markets)]
        out = out.drop(columns=["_market"])

    return out.reset_index(drop=True)
