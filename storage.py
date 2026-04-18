"""
Storage module - persists portfolios, trades, and group data
Uses Google Sheets as backend via gspread (configure secrets in Streamlit Cloud)
Falls back to local JSON for development
"""

import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

# Try to use Google Sheets if credentials available, else local file
USE_GSHEETS = False
try:
    import gspread
    from google.oauth2.service_account import Credentials

    if "gcp_service_account" in st.secrets:
        USE_GSHEETS = True
except Exception:
    USE_GSHEETS = False


LOCAL_DB_PATH = Path(".streamlit_db")
LOCAL_DB_PATH.mkdir(exist_ok=True)

GROUPS_FILE = LOCAL_DB_PATH / "groups.json"
TRADES_FILE = LOCAL_DB_PATH / "trades.json"
PORTFOLIOS_FILE = LOCAL_DB_PATH / "portfolios.json"


# ---------- Local JSON helpers ----------
def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------- Public API ----------
def register_group(group_number: int, nickname: str, captain: str, password: str) -> bool:
    """Registra un nuevo grupo. Retorna True si se creó, False si ya existe."""
    groups = _read_json(GROUPS_FILE, {})
    key = str(group_number)
    if key in groups:
        return False
    groups[key] = {
        "group_number": group_number,
        "nickname": nickname,
        "captain": captain,
        "password": password,
        "initial_capital": 100_000_000,
        "created_at": datetime.now().isoformat(),
    }
    _write_json(GROUPS_FILE, groups)
    # Initialize empty portfolio
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    portfolios[key] = {}  # {ticker: quantity}
    _write_json(PORTFOLIOS_FILE, portfolios)
    return True


def authenticate(group_number: int, password: str) -> dict | None:
    groups = _read_json(GROUPS_FILE, {})
    key = str(group_number)
    if key in groups and groups[key]["password"] == password:
        return groups[key]
    return None


def get_all_groups() -> dict:
    return _read_json(GROUPS_FILE, {})


def get_portfolio(group_number: int) -> dict:
    """Returns {ticker: quantity}"""
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    return portfolios.get(str(group_number), {})


def save_portfolio(group_number: int, portfolio: dict):
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    portfolios[str(group_number)] = portfolio
    _write_json(PORTFOLIOS_FILE, portfolios)


def record_trade(group_number: int, trade: dict):
    """Trade = {action, ticker, quantity, price, amount, timestamp}"""
    trades = _read_json(TRADES_FILE, {})
    key = str(group_number)
    if key not in trades:
        trades[key] = []
    trade["timestamp"] = datetime.now().isoformat()
    trades[key].append(trade)
    _write_json(TRADES_FILE, trades)


def get_trades(group_number: int) -> list:
    trades = _read_json(TRADES_FILE, {})
    return trades.get(str(group_number), [])


def get_all_trades() -> dict:
    return _read_json(TRADES_FILE, {})


def reset_all():
    """ADMIN: borra todo"""
    for f in [GROUPS_FILE, TRADES_FILE, PORTFOLIOS_FILE]:
        if f.exists():
            f.unlink()
