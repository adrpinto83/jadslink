"""Model for exchange rate tracking (USD -> VEF Bolívar venezolano)."""

from sqlalchemy import String, Numeric, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
from decimal import Decimal


class ExchangeRate(BaseModel):
    """Historial de tasas de cambio USD -> VEF (Bolívar venezolano)"""

    __tablename__ = "exchange_rates"

    rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'bcv_scraping', 'manual', 'api_fallback'
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ExchangeRate rate={self.rate} source={self.source} active={self.is_active}>"
