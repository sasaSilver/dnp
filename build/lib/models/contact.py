from sqlalchemy.orm import mapped_column, Mapped

from .base import Base


class ContactSchema(Base):
    __tablename__ = "contacts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(unique=True)    



