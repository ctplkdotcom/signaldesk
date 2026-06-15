from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Methodology(Base):
    __tablename__ = "methodologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    description: Mapped[str | None] = mapped_column(Text)
    input_data: Mapped[dict | None] = mapped_column(JSON)
    formula: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict | None] = mapped_column(JSON)
    limitations: Mapped[dict | None] = mapped_column(JSON)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Methodology {self.name} v{self.version}>"
