from sqlalchemy import Column, Integer, String, UniqueConstraint, Boolean
from sqlalchemy import DateTime, ARRAY
from sqlalchemy.sql import func

from settings import Base


class DrugClass(Base):
    __tablename__ = "drug_classes_urls"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), nullable=False, unique=True)
    url = Column(String(length=2048), nullable=False, unique=True)
    analyzed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add a composite unique constraint as well for extra safety
    __table_args__ = (UniqueConstraint('name', 'url', name='uix_name_url'),)


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), nullable=False, unique=True)
    url = Column(String(length=2048), nullable=False, unique=True)
    ndc_codes = Column(ARRAY(String(length=100)), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
