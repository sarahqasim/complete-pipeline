from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class EquipmentItem(Base):
    __tablename__ = "equipment_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    equipment_name: Mapped[str] = mapped_column(String(255), nullable=True)
    item_detail: Mapped[str] = mapped_column(String(512), nullable=True)
    qty: Mapped[str] = mapped_column(String(50), nullable=True)
    location_service: Mapped[str] = mapped_column(String(255), nullable=True)
    electrical: Mapped[str] = mapped_column(String(100), nullable=True)
    basis_of_design: Mapped[str] = mapped_column(String(255), nullable=True)
    manufacturers: Mapped[str] = mapped_column(String(512), nullable=True)
    warranty: Mapped[str] = mapped_column(String(255), nullable=True)
    training: Mapped[str] = mapped_column(String(255), nullable=True)
    spare_parts: Mapped[str] = mapped_column(String(255), nullable=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="unmatched")
