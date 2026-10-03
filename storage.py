"""
Storage module - Google Sheets backend con caching agresivo

Guarda números como strings con punto decimal para evitar problemas de locale
"""

import hashlib
import hmac
import secrets
import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re
import pandas as pd

INITIAL_CAPITAL = 100_000_000

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_GROUPS = "Groups"
TAB_PORTFOLIOS = "Portfolios"
TAB_CASH = "Cash"
TAB_TRADES = "Trades"

CACHE_TTL = 300  # 5 minutos (antes: 30 segundos)


def safe_float(value, default=0.0):
    if value is None or value == "":
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return float(default)
    s = re.sub(r"[^\d.,\-]", "", s)
    if not s:
        return float(default)
    if "." in s and "," in s:
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        if s.count(".") > 1:
            s = s.replace(".", "")
        else:
            parts = s.split(".")
            if len(parts[1]) == 3 and len(parts[0]) <= 3:
                s = s.replace(".", "")
    elif "," in s:
        if s.count(",") > 1:
            s = s.replace(",", "")
        else:
            parts = s.split(",")
            if len(parts[1]) == 3 and len(parts[0]) <= 3:
                s = s.replace(",", "")
            else:
                s = s.replace(",", ".")
    try:
        return float(s)
    except (ValueError, TypeError):
        return float(default)


# ---------------------------------------------------------------
# Contraseñas: se guardan como hash PBKDF2 (nunca en texto plano)
# ---------------------------------------------------------------
_PBKDF2_ITER = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode(), bytes.fromhex(salt), _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt}${digest.hex()}"


def _is_hashed(stored: str) -> bool:
    return str(stored).startswith("pbkdf2$")


def verify_password(password: str, stored) -> bool:
    stored = str(stored)
    if _is_hashed(stored):
        try:
            _, iters, salt, digest = stored.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", str(password).encode(), bytes.fromhex(salt), int(iters))
            return hmac.compare_digest(calc.hex(), digest)
        except (ValueError, TypeError):
            return False
    # Contraseñas antiguas en texto plano (se migran al iniciar sesión)
    return hmac.compare_digest(stored.encode(), str(password).encode())


def _group_public_info(r: dict) -> dict:
    return {
        "group_number": int(r["group_number"]),
        "nickname": r["nickname"],
        "captain": r["captain"],
        "initial_capital": INITIAL_CAPITAL,
        "created_at": r.get("created_at", ""),
    }


def _safe_read(func):
    """Reintenta hasta 4 veces con backoff exponencial ante errores 429."""
    for intento in range(4):
        try:
            return func()
        except Exception as e:
            if '429' in str(e) and intento < 3:
                time.sleep(2 ** intento)
            else:
                raise


@st.cache_resource(ttl=3600)
def _get_gsheet_client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


@st.cache_resource(ttl=3600)
def _get_sheet():
    client = _get_gsheet_client()
    sheet_name = st.secrets.get("sheet_name", "Capital Markets DB")
    return client.open(sheet_name)


@st.cache_resource(ttl=3600)
def _get_tab(tab_name: str):
    return _get_sheet().worksheet(tab_name)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _read_groups_records():
    return _safe_read(lambda: _get_tab(TAB_GROUPS).get_all_records())


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _read_portfolios_records():
    return _safe_read(lambda: _get_tab(TAB_PORTFOLIOS).get_all_records())


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _read_cash_records():
    return _safe_read(lambda: _get_tab(TAB_CASH).get_all_records())


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _read_trades_records():
    return _safe_read(lambda: _get_tab(TAB_TRADES).get_all_records())


TAB_SNAPSHOTS = "Snapshots"


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_snapshots() -> pd.DataFrame:
    """Fotos diarias del cierre (las escribe scheduler.py). Vacío si aún no hay."""
    cols = ["date", "group_number", "invested", "cash", "total_value", "return_pct", "cash_pct"]
    try:
        records = _safe_read(lambda: _get_tab(TAB_SNAPSHOTS).get_all_records())
    except Exception:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(records)
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=cols)
    df = df[df["date"].astype(str).str.strip() != ""].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["group_number"] = df["group_number"].astype(str).str.strip()
    for c in cols[2:]:
        if c in df.columns:
            df[c] = df[c].map(safe_float)
    return df.dropna(subset=["date"]).sort_values(["group_number", "date"])


def _invalidate_cache():
    _read_groups_records.clear()
    _read_portfolios_records.clear()
    _read_cash_records.clear()
    _read_trades_records.clear()


def register_group(group_number: int, nickname: str, captain: str, password: str) -> bool:
    rows = _read_groups_records()
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            return False
    tab = _get_tab(TAB_GROUPS)
    tab.append_row([
        group_number, nickname, captain, hash_password(password),
        datetime.now().isoformat(),
    ], value_input_option="RAW")
    cash_tab = _get_tab(TAB_CASH)
    cash_tab.append_row([group_number, INITIAL_CAPITAL], value_input_option="USER_ENTERED")
    _invalidate_cache()
    return True


def authenticate(group_number: int, password: str) -> dict | None:
    rows = _read_groups_records()
    for r in rows:
        if str(r.get("group_number")) != str(group_number):
            continue
        stored = r.get("password", "")
        if not verify_password(password, stored):
            return None
        if not _is_hashed(stored):
            _upgrade_password(group_number, password)
        return _group_public_info(r)
    return None


def _upgrade_password(group_number: int, password: str):
    """Reemplaza una contraseña antigua en texto plano por su hash."""
    try:
        tab = _get_tab(TAB_GROUPS)
        header = tab.row_values(1)
        pw_col = header.index("password") + 1 if "password" in header else 4
        col = tab.col_values(1)
        for i, val in enumerate(col):
            if i > 0 and str(val).strip() == str(group_number):
                tab.update_cell(i + 1, pw_col, hash_password(password))
                _read_groups_records.clear()
                return
    except Exception as e:
        print(f"No se pudo migrar la contraseña del grupo {group_number}: {e}")


def get_all_groups() -> dict:
    rows = _read_groups_records()
    result = {}
    for r in rows:
        key = str(r.get("group_number", "")).strip()
        if not key:
            continue
        result[key] = _group_public_info(r)
    return result


def get_portfolio(group_number: int) -> dict:
    rows = _read_portfolios_records()
    portfolio = {}
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            ticker = r.get("ticker")
            qty = safe_float(r.get("quantity", 0))
            if ticker and qty > 0:
                portfolio[ticker] = qty
    return portfolio


def save_portfolio(group_number: int, portfolio: dict):
    """Guarda las posiciones de un grupo con una sola escritura.

    Reutiliza las filas que ya tiene el grupo (sin borrar filas), de modo que
    las filas de otros grupos nunca se mueven aunque operen al mismo tiempo.
    """
    tab = _get_tab(TAB_PORTFOLIOS)
    all_rows = _safe_read(lambda: tab.get_all_values())
    own_rows = [
        i + 1 for i, row in enumerate(all_rows)
        if i > 0 and row and str(row[0]).strip() == str(group_number)
    ]
    new_rows = [
        [group_number, ticker, f"{float(qty):.6f}"]
        for ticker, qty in portfolio.items()
        if qty > 0.0001
    ]
    updates = []
    for idx, row_num in enumerate(own_rows):
        # Las filas sobrantes quedan como marcador del grupo (sin ticker y en 0)
        # para no dejar huecos: un hueco haría que append_rows escriba en medio.
        values = new_rows[idx] if idx < len(new_rows) else [group_number, "", "0"]
        updates.append({"range": f"A{row_num}:C{row_num}", "values": [values]})
    if updates:
        _safe_read(lambda: tab.batch_update(updates, value_input_option="RAW"))
    extra = new_rows[len(own_rows):]
    if extra:
        _safe_read(lambda: tab.append_rows(extra, value_input_option="RAW"))
    _invalidate_cache()


def _find_cash_row(group_number: int):
    tab = _get_tab(TAB_CASH)
    col = tab.col_values(1)
    for i, val in enumerate(col):
        if i == 0:
            continue
        if str(val).strip() == str(group_number):
            return i + 1
    return None


def get_cash(group_number: int) -> float:
    rows = _read_cash_records()
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            return safe_float(r.get("cash", INITIAL_CAPITAL), INITIAL_CAPITAL)
    tab = _get_tab(TAB_CASH)
    tab.append_row([group_number, INITIAL_CAPITAL], value_input_option="USER_ENTERED")
    _invalidate_cache()
    return float(INITIAL_CAPITAL)


def set_cash(group_number: int, amount: float):
    tab = _get_tab(TAB_CASH)
    row = _find_cash_row(group_number)
    amount = max(0.0, float(amount))
    if row is None:
        tab.append_row([group_number, amount], value_input_option="USER_ENTERED")
    else:
        tab.update_cell(row, 2, amount)
    _invalidate_cache()


def decrease_cash(group_number: int, amount: float) -> bool:
    current = get_cash(group_number)
    if amount > current + 0.01:
        return False
    set_cash(group_number, current - amount)
    return True


def increase_cash(group_number: int, amount: float):
    current = get_cash(group_number)
    set_cash(group_number, current + amount)


def record_trade(group_number: int, trade: dict):
    tab = _get_tab(TAB_TRADES)
    qty = float(trade.get("quantity", 0))
    price = float(trade.get("price", 0))
    amount = qty * price
    tab.append_row([
        group_number,
        datetime.now().isoformat(),
        trade.get("action", ""),
        trade.get("ticker", ""),
        f"{qty:.6f}",
        f"{price:.2f}",
        f"{amount:.2f}",
    ], value_input_option="RAW")
    _invalidate_cache()


def get_trades(group_number: int) -> list:
    rows = _read_trades_records()
    result = []
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            qty = safe_float(r.get("quantity", 0))
            price = safe_float(r.get("price", 0))
            result.append({
                "timestamp": r.get("timestamp", ""),
                "action": r.get("action", ""),
                "ticker": r.get("ticker", ""),
                "quantity": qty,
                "price": price,
                "amount": qty * price,
            })
    return result


def get_all_trades() -> dict:
    rows = _read_trades_records()
    result = {}
    for r in rows:
        key = str(r.get("group_number"))
        if not key or key == "":
            continue
        if key not in result:
            result[key] = []
        qty = safe_float(r.get("quantity", 0))
        price = safe_float(r.get("price", 0))
        result[key].append({
            "timestamp": r.get("timestamp", ""),
            "action": r.get("action", ""),
            "ticker": r.get("ticker", ""),
            "quantity": qty,
            "price": price,
            "amount": qty * price,
        })
    return result


def _remove_group_rows(tab_name: str, group_keys: set):
    """Elimina las filas de los grupos indicados con UNA sola escritura.

    Lee la pestaña completa, conserva las filas de otros grupos y reescribe
    el bloque de datos (rellenando con vacíos el espacio sobrante). Así el
    número de llamadas a la API no depende de cuántas filas haya.
    """
    tab = _get_tab(tab_name)
    all_rows = _safe_read(lambda: tab.get_all_values())
    if len(all_rows) <= 1:
        return
    data = all_rows[1:]
    keep = [r for r in data if not (r and str(r[0]).strip() in group_keys)]
    if len(keep) == len(data):
        return
    ncols = max(len(r) for r in all_rows)
    padded = [r + [""] * (ncols - len(r)) for r in keep]
    padded += [[""] * ncols] * (len(data) - len(keep))
    end_cell = gspread.utils.rowcol_to_a1(len(all_rows), ncols)
    _safe_read(lambda: tab.update(
        values=padded, range_name=f"A2:{end_cell}", value_input_option="RAW"
    ))


def _reset_cash(group_keys: set):
    """Pone el cash de los grupos en el capital inicial con UNA sola escritura."""
    tab = _get_tab(TAB_CASH)
    col = _safe_read(lambda: tab.col_values(1))
    updates, found = [], set()
    for i, val in enumerate(col):
        key = str(val).strip()
        if i == 0 or key not in group_keys:
            continue
        updates.append({"range": f"B{i + 1}", "values": [[INITIAL_CAPITAL]]})
        found.add(key)
    if updates:
        _safe_read(lambda: tab.batch_update(updates, value_input_option="USER_ENTERED"))
    missing = sorted(group_keys - found, key=lambda k: int(k) if k.isdigit() else 0)
    if missing:
        _safe_read(lambda: tab.append_rows(
            [[int(k) if k.isdigit() else k, INITIAL_CAPITAL] for k in missing],
            value_input_option="USER_ENTERED",
        ))


def _reset_groups(group_keys: set):
    if not group_keys:
        return
    _remove_group_rows(TAB_PORTFOLIOS, group_keys)
    _reset_cash(group_keys)
    _remove_group_rows(TAB_TRADES, group_keys)
    _invalidate_cache()


def reset_group(group_number: int):
    _reset_groups({str(group_number)})


def reset_all_groups():
    _invalidate_cache()
    groups = get_all_groups()
    _reset_groups({str(k).strip() for k in groups.keys()})


def delete_all_data():
    """Borra todo excepto los encabezados (una escritura por pestaña)."""
    for tab_name in [TAB_GROUPS, TAB_PORTFOLIOS, TAB_CASH, TAB_TRADES]:
        tab = _get_tab(tab_name)
        _safe_read(lambda: tab.batch_clear(["A2:Z"]))
    _invalidate_cache()
    get_game_start_date.clear()


def set_game_start_date(date_str: str) -> bool:
    try:
        sheet = _get_sheet()
        ws = sheet.worksheet("Cash")
        header = ws.acell('C1').value
        if header != 'game_start_date':
            ws.update(values=[["game_start_date"]], range_name="C1", value_input_option="RAW")
        ws.update(values=[[date_str]], range_name="C2", value_input_option="RAW")
        _invalidate_cache()
        get_game_start_date.clear()
        return True
    except Exception as e:
        print(f"Error setting game start date: {e}")
        return False


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_game_start_date() -> str:
    try:
        sheet = _get_sheet()
        ws = sheet.worksheet("Cash")
        value = ws.acell('C2').value
        if value and 'T' in str(value):
            value = str(value).split('T')[0]
        return value if value else None
    except Exception as e:
        print(f"Error getting game start date: {e}")
        return None
