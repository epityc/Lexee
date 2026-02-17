import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending_payment")  # active | pending_payment
    credits = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def generate_api_key() -> str:
        return f"lx_{uuid.uuid4().hex}"

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name!r} status={self.status} credits={self.credits}>"
