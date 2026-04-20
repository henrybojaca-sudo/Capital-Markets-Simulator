"""
Storage module - portafolios + cash disponible
"""

import json
from datetime import datetime
from pathlib import Path
import streamlit as st

LOCAL_DB_PATH = Path(".streamlit_db")
LOCAL_DB_PATH.mkdir(exist_ok=True)

GROUPS_FILE = LOCAL_DB_PATH / "groups.json"
TRADES_FILE = LOCAL_DB_PATH / "trades.json"
PORTFOLIOS_FILE = LOCAL_DB_PATH / "portfolios.json"
CASH_FILE = LOCAL_DB_PATH / "cash.json"

INITIAL_CAPITAL = 100_000_000


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------- Groups ----------
def register_group(group_number: int, nickname: str, captain: str, password: str) -> bool:
    groups = _read_json(GROUPS_FILE, {})
    key = str(group_number)
    if key in groups:
        return False
    groups[key] = {
        "group_number": group_number,
        "nickname": nickname,
        "captain": captain,
        "password": password,
        "initial_capital": INITIAL_CAPITAL,
        "created_at": datetime.now().isoformat(),
    }
    _write_json(GROUPS_FILE, groups)

    # Initialize portfolio (empty) + cash (full initial capital)
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    portfolios[key] = {}
    _write_json(PORTFOLIOS_FILE, portfolios)

    cash = _read_json(CASH_FILE, {})
    cash[key] = INITIAL_CAPITAL
    _write_json(CASH_FILE, cash)

    return True


def authenticate(group_number: int, password: str) -> dict | None:
    groups = _read_json(GROUPS_FILE, {})
    key = str(group_number)
    if key in groups and groups[key]["password"] == password:
        return groups[key]
    return None


def get_all_groups() -> dict:
    return _read_json(GROUPS_FILE, {})


# ---------- Portfolio ----------
def get_portfolio(group_number: int) -> dict:
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    return portfolios.get(str(group_number), {})


def save_portfolio(group_number: int, portfolio: dict):
    portfolios = _read_json(PORTFOLIOS_FILE, {})
    portfolios[str(group_number)] = portfolio
    _write_json(PORTFOLIOS_FILE, portfolios)


# ---------- Cash ----------
def get_cash(group_number: int) -> float:
    """Returns available cash for the group"""
    cash = _read_json(CASH_FILE, {})
    key = str(group_number)
    # If not found, assume full initial capital (for legacy groups)
    if key not in cash:
        cash[key] = INITIAL_CAPITAL
        _write_json(CASH_FILE, cash)
    return float(cash[key])


def set_cash(group_number: int, amount: float):
    cash = _read_json(CASH_FILE, {})
    cash[str(group_number)] = max(0.0, float(amount))
    _write_json(CASH_FILE, cash)


def decrease_cash(group_number: int, amount: float) -> bool:
    """Returns False if not enough cash"""
    current = get_cash(group_number)
    if amount > current + 0.01:  # tolerance for rounding
        return False
    set_cash(group_number, current - amount)
    return True


def increase_cash(group_number: int, amount: float):
    current = get_cash(group_number)
    set_cash(group_number, current + amount)


# ---------- Trades ----------
def record_trade(group_number: int, trade: dict):
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
    for f in [GROUPS_FILE, TRADES_FILE, PORTFOLIOS_FILE, CASH_FILE]:
        if f.exists():
            f.unlink()
