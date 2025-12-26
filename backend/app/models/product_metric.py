from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ProductMetric(Base):
    __tablename__ = "product_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"))
    score: Mapped[int]
    explanation: Mapped[str]

    # Для легкого доступа к имени метрики
    metric_info: Mapped["Metric"] = relationship(lazy="joined")

    def __repr__(self):
        return f"<Metric(id={self.id}, product_id='{self.product_id}', metric_id={self.metric_id}, score={self.score}', explanation={self.explanation}')>"