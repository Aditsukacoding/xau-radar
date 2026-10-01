from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime, timezone
from typing import Optional


class EconomicEventBase(BaseModel):
    currency: str = "USD"
    event_title: str
    impact_level: str = "HIGH"
    scheduled_at: datetime
    actual_value: Optional[str] = None
    forecast_value: Optional[str] = None
    previous_value: Optional[str] = None
    unit: Optional[str] = None
    sentiment_impact: Optional[str] = None


class EconomicEventCreate(EconomicEventBase):
    external_id: Optional[str] = None


class EconomicEventResponse(EconomicEventBase):
    id: int
    external_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("scheduled_at", "created_at")
    def serialize_datetime_as_utc(self, dt: datetime) -> str:
        """Ensure all datetime fields are serialized as UTC ISO-8601 with +00:00 suffix.
        SQLite stores naive datetimes — we treat them as UTC explicitly."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            # Naive datetime from SQLite — assume stored as UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()  # e.g. "2026-09-30T12:30:00+00:00"

