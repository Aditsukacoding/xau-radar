from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class InstrumentBase(BaseModel):
    symbol: str
    name: str
    category: str = "commodity"
    base_currency: str = "XAU"
    quote_currency: str = "USD"
    pip_decimal: int = 2
    is_active: bool = True


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentResponse(InstrumentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
