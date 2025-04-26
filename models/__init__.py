from settings import Base, engine, SessionLocal
from .dailymed import DrugClass, Drug
from .analytics import (
    AnalyticsResult, NDCAnalysis, DrugClassAnalysis,
    NameAnalysis, URLAnalysis, TimeAnalysis, TextMiningResult,
    DrugRelationship
)

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Export models and database setup
__all__ = [
    'Base', 'engine', 'SessionLocal',
    'DrugClass', 'Drug', 'init_db',
    'AnalyticsResult', 'NDCAnalysis', 'DrugClassAnalysis',
    'NameAnalysis', 'URLAnalysis', 'TimeAnalysis',
    'TextMiningResult', 'DrugRelationship'
]