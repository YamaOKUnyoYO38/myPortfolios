"""
ポートフォリオの永続化（JSON ファイル）。
削除操作以外ではリストが消えないよう、永続化パスを固定する。
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

# 環境変数 PORTFOLIO_DATA_DIR で上書き可能（例: Render の永続ボリュームパス）
# 未設定時はアプリと同じディレクトリの data フォルダに保存（終了後も残る）
_DATA_DIR = os.environ.get("PORTFOLIO_DATA_DIR")
if _DATA_DIR:
    DEFAULT_PATH = Path(_DATA_DIR) / "portfolios.json"
else:
    _app_dir = Path(__file__).resolve().parent
    DEFAULT_PATH = _app_dir / "data" / "portfolios.json"

def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# アプリ起動時から保存先ディレクトリを存在させ、再起動後も確実に読み出せるようにする
_ensure_dir(DEFAULT_PATH)


def _get_path(file_path: Path | str | None) -> Path:
    """保存パスを返す。指定がなければ DEFAULT_PATH。"""
    return Path(file_path) if file_path else DEFAULT_PATH


def load_portfolios(file_path: Path | str | None = None) -> list[dict]:
    """
    ポートフォリオ一覧を読み込む。
    各要素: {"id": str, "name": str, "symbols": list[str], "created_at": str, "view_count": int}
    """
    path = _get_path(file_path)
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
    """ポートフォリオ一覧を保存する。上書き破損を防ぐため一時ファイルに書き出してからリネーム。削除操作以外でリストが消えないよう、書き込み後にフラッシュする。"""
    path = _get_path(file_path)
    _ensure_dir(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"portfolios": portfolios}, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except OSError:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


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


def _symbol_from_entry(entry: str) -> str:
    """保存形式 '表示名|銘柄コード' または '銘柄コード' から銘柄コード部分を返す。"""
    if "|" in entry:
        return entry.split("|", 1)[-1].strip() or entry
    return entry


def add_symbol_to_portfolio(
    portfolio_id: str,
    symbol: str,
    display_name: str | None = None,
    file_path: Path | str | None = None,
) -> bool:
    """ポートフォリオに銘柄を1件追加（重複は追加しない）。display_name がある場合は '表示名|symbol' で保存し一覧で銘柄名を表示する。"""
    if not (symbol and str(symbol).strip()):
        return False
    symbol = str(symbol).strip()
    entry = f"{display_name.strip()}|{symbol}" if (display_name and str(display_name).strip()) else symbol
    portfolios = load_portfolios(file_path)
    for p in portfolios:
        if p.get("id") == portfolio_id:
            syms = p.get("symbols") or []
            existing_codes = {_symbol_from_entry(s) for s in syms}
            if symbol not in existing_codes:
                syms.append(entry)
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
