from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy_utils import ChoiceType
import uuid
from database.database import Base


class User(Base):
    """ORM model for the Users table.
    This class defines the structure of the Users table in the database.
    """

    ROLE = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('curator', 'Curator'),
        ('viewer', 'Viewer'),
    )
    __tablename__ = 'Users'

    user_id = Column(String(100), primary_key=True, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    user_name = Column(String(100), nullable=False, unique=True)
    role = Column(ChoiceType(ROLE), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"User(user_name={self.user_name}, role={self.role})"