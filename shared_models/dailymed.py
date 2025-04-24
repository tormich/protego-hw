from sqlalchemy import Column, Integer, String
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from settings import Base


class DrugClass(Base):
    __tablename__ = "drug_classes_urls"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), nullable=False)
    url = Column(String(length=2048), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

