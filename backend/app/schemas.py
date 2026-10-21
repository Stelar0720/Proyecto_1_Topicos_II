"""Esquemas Pydantic (validación de entrada/salida de la API)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import VALID_STATUSES
from .utils import PhoneError, normalize_cl_phone, to_local_naive


# ---------- Servicios ----------
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    duration_min: int = Field(30, ge=5, le=480)
    price: int = Field(0, ge=0)
    active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    duration_min: Optional[int] = Field(None, ge=5, le=480)
    price: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class ServiceOut(ServiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Citas ----------
class AppointmentCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=120)
    customer_phone: str = Field(..., examples=["+56 9 4291 6570"])
    service_id: int
    start_at: datetime = Field(..., description="Inicio de la cita (ISO 8601)")
    notes: str = Field("", max_length=300)

    @field_validator("customer_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        try:
            return normalize_cl_phone(v)
        except PhoneError as e:
            raise ValueError(str(e))

    @field_validator("start_at")
    @classmethod
    def _naive_local(cls, v: datetime) -> datetime:
        return to_local_naive(v)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    customer_phone: str
    service_id: int
    start_at: datetime
    end_at: datetime
    status: str
    notes: str
    reminder_sent: bool
    created_at: datetime
    service: Optional[ServiceOut] = None


# ---------- Identidad de cliente ----------
class CustomerChallengeRequest(BaseModel):
    customer_phone: str

    @field_validator("customer_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        try:
            return normalize_cl_phone(v)
        except PhoneError as e:
            raise ValueError(str(e))


class CustomerChallengeVerify(CustomerChallengeRequest):
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class CustomerTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CustomerProfileUpdate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=120)


class CustomerProfileOut(BaseModel):
    id: str
    display_name: str
    phone: str


class CustomerAppointmentCreate(BaseModel):
    service_id: int
    start_at: datetime
    notes: str = Field("", max_length=300)

    @field_validator("start_at")
    @classmethod
    def _naive_local(cls, v: datetime) -> datetime:
        return to_local_naive(v)


class AppointmentStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Estado inválido. Debe ser uno de: {sorted(VALID_STATUSES)}")
        return v


# ---------- Otros ----------
class CalendarDayOut(BaseModel):
    date: date
    status: Literal["available", "full", "closed", "past"]
    available_count: int


class AvailabilityCalendarOut(BaseModel):
    service_id: int
    duration_min: int
    month: str
    days: list[CalendarDayOut]


# ---------- Previsión de demanda (HU-03) ----------
class ForecastHistoryDayOut(BaseModel):
    date: date
    demand: int
    closed: bool


class ForecastDayOut(BaseModel):
    date: date
    forecast: Optional[float]
    closed: bool
    basis: Literal["weekday_average", "overall_average", "closed", "no_data"]


class ForecastWarningOut(BaseModel):
    code: str
    message: str


class ForecastBacktestOut(BaseModel):
    cutoff: date
    days: int
    evaluated_days: int
    mae: float


class DemandForecastOut(BaseModel):
    cutoff: date
    history_start: date
    history_end: date
    history_days: int
    forecast_days: int
    method: str
    demand_definition: str
    included_statuses: list[str]
    excluded_statuses: list[str]
    closed_weekdays: list[int]
    observed_days: int
    observed_appointments: int
    warnings: list[ForecastWarningOut]
    history: list[ForecastHistoryDayOut]
    forecast: list[ForecastDayOut]
    backtest: Optional[ForecastBacktestOut] = None


class ConfigOut(BaseModel):
    business_name: str
    timezone: str
    currency: str
    open_hour: int
    close_hour: int
    slot_interval_minutes: int
    closed_weekdays: list[int]


class StatsOut(BaseModel):
    total: int
    pending: int
    confirmed: int
    cancelled: int
    done: int
    upcoming: int


class MessageOut(BaseModel):
    detail: str
