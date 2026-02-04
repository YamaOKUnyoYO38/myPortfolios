"""
ポートフォリオの永続化（JSON ファイル）。
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("data") / "portfolios.json"


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_portfolios(file_path: Path | str | None = None) -> list[dict]:
    """
    ポートフォリオ一覧を読み込む。
    各要素: {"id": str, "name": str, "symbols": list[str], "created_at": str, "view_count": int}
    """
    path = Path(file_path) if file_path else DEFAULT_PATH
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    raw = data["portfolios"] if isinstance(data, dict) and "portfolios" in data else (data if isinstance(data, list) else [])
    # 後方互換: created_at, view_count がない場合は付与
    now = datetime.now().isoformat()
    for p in raw:
        if "created_at" not in p:
            p["created_at"] = now
        if "view_count" not in p:
            p["view_count"] = 0
    return raw


def save_portfolios(portfolios: list[dict], file_path: Path | str | None = None) -> None:
    """ポートフォリオ一覧を保存する。"""
    path = Path(file_path) if file_path else DEFAULT_PATH
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"portfolios": portfolios}, f, ensure_ascii=False, indent=2)


def create_portfolio(name: str, file_path: Path | str | None = None) -> dict:
    """新規ポートフォリオを作成して保存し、作成した辞書を返す。"""
    portfolios = load_portfolios(file_path)
    new_id = str(uuid.uuid4())
    new_p = {"id": new_id, "name": name, "symbols": [], "created_at": datetime.now().isoformat(), "view_count": 0}
    portfolios.append(new_p)
    save_portfolios(portfolios, file_path)
    return new_p


def update_portfolio(portfolio_id: str, name: str | None = None, symbols: list[str] | None = None, file_path: Path | str | None = None) -> bool:
    """ポートフォリオを更新。name または symbols を指定。"""
    portfolios = load_portfolios(file_path)
    for p in portfolios:
        if p.get("id") == portfolio_id:
            if name is not None:
                p["name"] = name
            if symbols is not None:
                p["symbols"] = list(symbols)
            save_portfolios(portfolios, file_path)
            return True
    return False


def delete_portfolio(portfolio_id: str, file_path: Path | str | None = None) -> bool:
    """ポートフォリオを削除。"""
    portfolios = load_portfolios(file_path)
    new_list = [p for p in portfolios if p.get("id") != portfolio_id]
    if len(new_list) == len(portfolios):
        return False
    save_portfolios(new_list, file_path)
    return True


def add_symbol_to_portfolio(portfolio_id: str, symbol: str, file_path: Path | str | None = None) -> bool:
    """ポートフォリオに銘柄を1件追加（重複は追加しない）。"""
    portfolios = load_portfolios(file_path)
    for p in portfolios:
        if p.get("id") == portfolio_id:
            syms = p.get("symbols") or []
            if symbol not in syms:
                syms.append(symbol)
                p["symbols"] = syms
                save_portfolios(portfolios, file_path)
            return True
    return False


def increment_view_count(portfolio_id: str, file_path: Path | str | None = None) -> bool:
    """閲覧回数を1増やす。"""
    portfolios = load_portfolios(file_path)
    for p in portfolios:
        if p.get("id") == portfolio_id:
            p["view_count"] = p.get("view_count", 0) + 1
            save_portfolios(portfolios, file_path)
            return True
    return False
