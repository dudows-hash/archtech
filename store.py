import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR, HISTORY_PATH

COLUMNS = [
    "fila",
    "product_architect",
    "sai",
    "arch_copilot",
    "data_review",
    "supervisor",
    "concluido",
]

COLUMN_LABELS = {
    "fila": "Fila",
    "product_architect": "Product Architect",
    "sai": "SAI",
    "arch_copilot": "Arch Copilot",
    "data_review": "Data Review",
    "supervisor": "Supervisor",
    "concluido": "Concluido",
}

_lock = threading.RLock()
_board = {column: [] for column in COLUMNS}
_history = []
_current_id = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load():
    global _history
    _ensure_data_dir()
    path = Path(HISTORY_PATH)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            _history = payload.get("history", [])
    else:
        _history = []


def persist():
    _ensure_data_dir()
    with Path(HISTORY_PATH).open("w", encoding="utf-8") as handle:
        json.dump({"history": _history}, handle, ensure_ascii=False, indent=2)


def snapshot():
    with _lock:
        return {
            "columns": COLUMNS,
            "labels": COLUMN_LABELS,
            "board": deepcopy(_board),
            "current_id": _current_id,
            "history": deepcopy(_history),
        }


def reset_board():
    global _board, _current_id
    with _lock:
        _board = {column: [] for column in COLUMNS}
        _current_id = None
        return snapshot()


def _find_on_board(card_id):
    for column in COLUMNS:
        for index, card in enumerate(_board[column]):
            if card["id"] == card_id:
                return column, index, card
    return None, None, None


def create_card(titulo, dor, custo, cliente):
    global _board, _current_id
    cliente = (cliente or "").strip()
    titulo = (titulo or "").strip()
    card = {
        "id": str(uuid.uuid4()),
        "titulo": titulo,
        "dor": (dor or "").strip(),
        "custo": custo,
        "cliente": cliente,
        "status": "fila",
        "created_at": _now(),
        "completed_at": None,
        "artifacts": {
            "prd": "",
            "adr": "",
            "codigo": "",
            "review": "",
            "checkpoint": "",
        },
        "notion_url": None,
        "notion_error": None,
        "title_display": f"[{cliente}] {titulo}" if cliente else titulo,
    }
    with _lock:
        _board = {column: [] for column in COLUMNS}
        _board["fila"].append(card)
        _current_id = card["id"]
        return deepcopy(card)


def get_card(card_id):
    with _lock:
        _, _, card = _find_on_board(card_id)
        if card:
            return deepcopy(card)
        for card in _history:
            if card["id"] == card_id:
                return deepcopy(card)
    return None


def move_card(card_id, target_column, artifacts=None, status=None):
    with _lock:
        column, index, card = _find_on_board(card_id)
        if not card:
            return None
        del _board[column][index]
        if artifacts:
            card["artifacts"].update(artifacts)
        card["status"] = status or target_column
        if target_column == "concluido":
            card["completed_at"] = _now()
        _board[target_column].append(card)
        return deepcopy(card)


def complete_card(card_id, artifacts, notion_url=None, notion_error=None):
    card = move_card(card_id, "concluido", artifacts=artifacts, status="concluido")
    if not card:
        return None
    with _lock:
        _, _, live = _find_on_board(card_id)
        if live:
            live["notion_url"] = notion_url
            live["notion_error"] = notion_error
            live["artifacts"] = artifacts
            card = deepcopy(live)
        replaced = False
        for index, item in enumerate(_history):
            if item["id"] == card_id:
                _history[index] = deepcopy(card)
                replaced = True
                break
        if not replaced:
            _history.insert(0, deepcopy(card))
        persist()
        return deepcopy(card)


def update_card_notion(card_id, url=None, error=None):
    with _lock:
        updated = None
        _, _, card = _find_on_board(card_id)
        if card:
            card["notion_url"] = url
            card["notion_error"] = error
            updated = deepcopy(card)
        for index, item in enumerate(_history):
            if item["id"] == card_id:
                _history[index]["notion_url"] = url
                _history[index]["notion_error"] = error
                updated = deepcopy(_history[index])
        if updated:
            persist()
        return updated


def list_history():
    with _lock:
        return deepcopy(_history)


load()
