from settings import Base, engine, SessionLocal
from .dailymed import DrugClass

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Export models and database setup
__all__ = ['Base', 'engine', 'SessionLocal', 'DrugClass', 'init_db'] 