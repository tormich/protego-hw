from sqlalchemy import Column, Integer, String
from env import Base


class DrugClass(Base):
    __tablename__ = "drug_classes_urls"
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255))
    url = Column(String(length=2048))

