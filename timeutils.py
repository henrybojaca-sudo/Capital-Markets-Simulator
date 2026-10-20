"""
Utilidades de fecha y hora en horario de Bogotá (UTC-5, sin horario de verano).

El servidor (Streamlit Cloud, GitHub Actions) corre en UTC, así que nunca se
debe usar datetime.now() / date.today() sin zona horaria.
"""

from datetime import datetime, timedelta, timezone

BOGOTA = timezone(timedelta(hours=-5), "COT")


def now_bogota() -> datetime:
    """Fecha y hora actual en Bogotá (con zona horaria)."""
    return datetime.now(BOGOTA)


def today_bogota():
    """Fecha de hoy en Bogotá."""
    return now_bogota().date()


def to_bogota_str(value) -> str:
    """Convierte un timestamp ISO guardado a hora de Bogotá sin zona ('YYYY-MM-DDTHH:MM:SS').

    Los registros antiguos se guardaron sin zona horaria con la hora del
    servidor (UTC), por eso un valor sin zona se interpreta como UTC.
    """
    text = str(value or "").strip()
    if not text:
        return text
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return text
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BOGOTA).replace(tzinfo=None).isoformat(timespec="seconds")
