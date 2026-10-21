"""HU-03 — Previsión de demanda a partir del histórico de reservas.

Método (simple, reproducible y explicable): promedio por día de la semana.
Para cada día futuro se promedia la demanda observada de ese mismo día de la
semana dentro de una ventana histórica (28 días por defecto). No se entrena
ningún modelo ni se llama a una API de IA.

Definiciones acordadas:

- **Demanda de un día** = cantidad de citas cuyo inicio cae ese día y cuyo
  estado es `pending`, `confirmed` o `done`.
- Las citas **canceladas se excluyen** (no representan demanda efectiva). Las
  citas eliminadas no existen en la base y tampoco se cuentan.
- **Fecha de corte** = inicio del día actual (hora local del negocio). Sólo se
  usan citas con `start_at` anterior al corte **y** `created_at` anterior al
  corte: es información que ya se conocía antes de predecir.
- Los **días cerrados** (configuración `closed_weekdays`) se pronostican como 0
  y se marcan `closed=true`; no se inventa demanda para ellos.

Limitaciones: la media por día de la semana no captura tendencias, feriados,
promociones ni estacionalidad; con pocos datos es poco fiable (se advierte) y
sin datos no se entrega ninguna cifra (la previsión es `null`).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from statistics import fmean

from sqlalchemy.orm import Session

from . import models
from .config import settings
from .utils import local_now

# Estados que representan demanda real. `cancelled` queda fuera a propósito.
DEMAND_STATUSES = frozenset(
    {models.STATUS_PENDING, models.STATUS_CONFIRMED, models.STATUS_DONE}
)

DEFAULT_HISTORY_DAYS = 28
FORECAST_DAYS = 7
# Debajo de este número de días con observaciones se advierte "pocos datos".
MIN_HISTORY_DAYS = 14

METHOD_DESCRIPTION = (
    "Promedio de la demanda por día de la semana en la ventana histórica. "
    "Cada día de la ventana cuenta como observación; los días abiertos sin "
    "citas cuentan como 0. Para cada día futuro se usa la media de ese mismo "
    "día de la semana. Días cerrados: previsión 0. Sin datos: sin previsión "
    "(null)."
)
DEMAND_DEFINITION = (
    "Se cuenta una cita por su día de inicio si su estado es pending, "
    "confirmed o done. Las citas canceladas se excluyen. Sólo se usan citas "
    "creadas antes de la fecha de corte."
)


def _window_start(cutoff: date, history_days: int) -> date:
    return cutoff - timedelta(days=history_days)


def day_counts(
    db: Session, cutoff: date, history_days: int = DEFAULT_HISTORY_DAYS
) -> dict[date, int]:
    """Demanda por día en [cutoff - history_days, cutoff), sólo info previa al corte."""
    start = _window_start(cutoff, history_days)
    cutoff_dt = datetime.combine(cutoff, time.min)
    rows = (
        db.query(models.Appointment.start_at)
        .filter(
            models.Appointment.start_at >= datetime.combine(start, time.min),
            models.Appointment.start_at < cutoff_dt,
            models.Appointment.created_at < cutoff_dt,
            models.Appointment.status.in_(DEMAND_STATUSES),
        )
        .all()
    )
    counts: dict[date, int] = defaultdict(int)
    for (start_at,) in rows:
        counts[start_at.date()] += 1
    return dict(counts)


def weekday_means(counts: dict[date, int]) -> dict[int, float]:
    """Media de demanda por día de la semana (0=lunes … 6=domingo)."""
    buckets: dict[int, list[int]] = defaultdict(list)
    for day, value in counts.items():
        buckets[day.weekday()].append(value)
    return {weekday: fmean(values) for weekday, values in buckets.items()}


def forecast_from_counts(
    counts: dict[date, int],
    start_date: date,
    days: int = FORECAST_DAYS,
    closed_weekdays: set[int] | None = None,
) -> list[dict]:
    """Genera la previsión para `days` días desde `start_date` usando `counts`."""
    closed = settings.closed_weekdays_set if closed_weekdays is None else closed_weekdays
    means = weekday_means(counts)
    overall = fmean(counts.values()) if counts else None

    result: list[dict] = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        weekday = day.weekday()
        if weekday in closed:
            result.append(
                {"date": day, "forecast": 0.0, "closed": True, "basis": "closed"}
            )
        elif weekday in means:
            result.append(
                {
                    "date": day,
                    "forecast": round(means[weekday], 2),
                    "closed": False,
                    "basis": "weekday_average",
                }
            )
        elif overall is not None:
            result.append(
                {
                    "date": day,
                    "forecast": round(overall, 2),
                    "closed": False,
                    "basis": "overall_average",
                }
            )
        else:
            result.append(
                {"date": day, "forecast": None, "closed": False, "basis": "no_data"}
            )
    return result


def _warnings(observed_days: int) -> list[dict]:
    if observed_days == 0:
        return [
            {
                "code": "no_data",
                "message": (
                    "No hay citas históricas utilizables. No se inventa demanda: "
                    "la previsión queda vacía hasta acumular datos."
                ),
            }
        ]
    if observed_days < MIN_HISTORY_DAYS:
        return [
            {
                "code": "insufficient_data",
                "message": (
                    f"Sólo hay {observed_days} día(s) con datos (mínimo "
                    f"recomendado: {MIN_HISTORY_DAYS}). La previsión es "
                    "orientativa y puede variar mucho."
                ),
            }
        ]
    return []


def backtest(
    db: Session,
    cutoff: date,
    history_days: int = DEFAULT_HISTORY_DAYS,
    days: int = FORECAST_DAYS,
) -> dict | None:
    """Comparación retrospectiva: predice [corte - 7, corte) y mide el error MAE.

    Devuelve `None` si antes de ese corte retrospectivo no hay suficientes días
    con datos. Sólo se evalúan días abiertos (los cerrados se pronostican 0).
    """
    back_cutoff = cutoff - timedelta(days=days)
    history = day_counts(db, back_cutoff, history_days)
    if len(history) < MIN_HISTORY_DAYS:
        return None

    back_start = _window_start(back_cutoff, history_days)
    averaging_counts = {
        back_start + timedelta(days=offset): history.get(
            back_start + timedelta(days=offset), 0
        )
        for offset in range(history_days)
    }
    predicted = forecast_from_counts(averaging_counts, back_cutoff, days)
    actual = day_counts(db, cutoff, days)

    errors: list[float] = []
    for item in predicted:
        if item["closed"] or item["forecast"] is None:
            continue
        observed = actual.get(item["date"], 0)
        errors.append(abs(item["forecast"] - observed))

    if not errors:
        return None
    return {
        "cutoff": back_cutoff.isoformat(),
        "days": days,
        "evaluated_days": len(errors),
        "mae": round(fmean(errors), 2),
    }


def build_forecast(
    db: Session,
    cutoff: date | None = None,
    history_days: int = DEFAULT_HISTORY_DAYS,
    days: int = FORECAST_DAYS,
) -> dict:
    """Arma la respuesta completa del panel para la fecha de corte indicada."""
    cutoff = cutoff or local_now().date()
    counts = day_counts(db, cutoff, history_days)
    start = _window_start(cutoff, history_days)

    # Días abiertos sin citas son observaciones con demanda 0. Si no hay ninguna
    # cita, no se promedia nada: la previsión queda null (no se inventa demanda).
    if counts:
        averaging_counts = {
            start + timedelta(days=offset): counts.get(start + timedelta(days=offset), 0)
            for offset in range(history_days)
        }
    else:
        averaging_counts = {}
    forecast = forecast_from_counts(averaging_counts, cutoff, days)
    closed = settings.closed_weekdays_set
    observed_days = len(counts)

    return {
        "cutoff": cutoff.isoformat(),
        "history_start": start.isoformat(),
        "history_end": (cutoff - timedelta(days=1)).isoformat(),
        "history_days": history_days,
        "forecast_days": days,
        "method": METHOD_DESCRIPTION,
        "demand_definition": DEMAND_DEFINITION,
        "included_statuses": sorted(DEMAND_STATUSES),
        "excluded_statuses": [models.STATUS_CANCELLED],
        "closed_weekdays": sorted(closed),
        "observed_days": observed_days,
        "observed_appointments": sum(counts.values()),
        "warnings": _warnings(observed_days),
        "history": [
            {
                "date": (start + timedelta(days=offset)).isoformat(),
                "demand": counts.get(start + timedelta(days=offset), 0),
                "closed": (start + timedelta(days=offset)).weekday() in closed,
            }
            for offset in range(history_days)
        ],
        "forecast": [
            {
                "date": item["date"].isoformat(),
                "forecast": item["forecast"],
                "closed": item["closed"],
                "basis": item["basis"],
            }
            for item in forecast
        ],
        "backtest": backtest(db, cutoff, history_days, days),
    }
