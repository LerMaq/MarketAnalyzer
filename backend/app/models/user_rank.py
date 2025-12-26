from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserRank(Base):
    __tablename__ = "user_ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    expires_at: Mapped[datetime]

    user: Mapped["User"] = relationship(back_populates="ranks")

    def __repr__(self):
        return f"<UserRank(id={self.id}, user_id='{self.user_id}', rank_id={self.rank_id}, expires_at={self.expires_at})>"