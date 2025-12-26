from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Rank(Base):
    __tablename__ = "ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] # free, premium, ultra
    level: Mapped[int]

    def __repr__(self):
        return f"<Rank(id={self.id}, name='{self.name}', level={self.level})>"