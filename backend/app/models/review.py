from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int]
    author_name: Mapped[str]
    review_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"<Review(id={self.id}, product_id='{self.product_id}', text={self.text}, rating='{self.rating}', author_name='{self.author_name}', review_date='{self.review_date}')>"