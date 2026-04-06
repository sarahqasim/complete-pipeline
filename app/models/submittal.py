from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SubmittalItem(Base):
    __tablename__ = "submittal_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=True)
    has_drawing_match: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_spec: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_drawing: Mapped[str] = mapped_column(Text, nullable=True)
