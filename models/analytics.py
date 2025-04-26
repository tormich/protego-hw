"""
Database models for analytics results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from settings import Base


class AnalyticsResult(Base):
    """Base model for analytics results."""

    __tablename__ = "analytics_results"

    id = Column(Integer, primary_key=True)
    analyzer_name = Column(String(255), nullable=False)
    result_type = Column(String(255), nullable=False)
    result_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AnalyticsResult(id={self.id}, analyzer={self.analyzer_name}, type={self.result_type})>"


class NDCAnalysis(Base):
    """Model for NDC code analysis results."""

    __tablename__ = "ndc_analysis"

    id = Column(Integer, primary_key=True)
    ndc_code = Column(String(100), nullable=False, unique=True)
    drug_count = Column(Integer, nullable=False, default=0)
    is_shared = Column(Integer, nullable=False, default=0)  # 0=unique, 1=shared
    manufacturer_prefix = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<NDCAnalysis(ndc_code={self.ndc_code}, drug_count={self.drug_count})>"


class DrugClassAnalysis(Base):
    """Model for drug classification analysis results."""

    __tablename__ = "drug_class_analysis"

    id = Column(Integer, primary_key=True)
    drug_class_id = Column(Integer, ForeignKey("drug_classes_urls.id"), nullable=False)
    drug_count = Column(Integer, nullable=False, default=0)
    cross_classification_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to the drug class
    drug_class = relationship("DrugClass", backref="analysis")

    def __repr__(self):
        return f"<DrugClassAnalysis(drug_class_id={self.drug_class_id}, drug_count={self.drug_count})>"


class NameAnalysis(Base):
    """Model for drug name analysis results."""

    __tablename__ = "name_analysis"

    id = Column(Integer, primary_key=True)
    pattern_type = Column(String(50), nullable=False)  # prefix, suffix, full
    pattern = Column(String(255), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    is_brand = Column(Integer, nullable=True)  # 0=generic, 1=brand, NULL=unknown
    avg_length = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<NameAnalysis(pattern={self.pattern}, count={self.count})>"


class URLAnalysis(Base):
    """Model for URL pattern analysis results."""

    __tablename__ = "url_analysis"

    id = Column(Integer, primary_key=True)
    pattern = Column(String(255), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    avg_depth = Column(Float, nullable=True)
    domain = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<URLAnalysis(pattern={self.pattern}, count={self.count})>"


class TimeAnalysis(Base):
    """Model for time-based analysis results."""

    __tablename__ = "time_analysis"

    id = Column(Integer, primary_key=True)
    time_period = Column(String(50), nullable=False)  # day, week, month, year
    period_start = Column(DateTime(timezone=True), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TimeAnalysis(period={self.time_period}, count={self.count})>"


# Association table for drug relationships in network analysis
drug_relationships = Table(
    'drug_relationships',
    Base.metadata,
    Column('source_drug_id', Integer, ForeignKey('drugs.id'), primary_key=True),
    Column('target_drug_id', Integer, ForeignKey('drugs.id'), primary_key=True),
    Column('relationship_type', String(50), nullable=False),
    Column('weight', Float, nullable=False, default=1.0),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class TextMiningResult(Base):
    """Model for text mining results."""

    __tablename__ = "text_mining_results"

    id = Column(Integer, primary_key=True)
    term = Column(String(255), nullable=False)
    term_type = Column(String(50), nullable=False)  # name, ingredient, dosage_form
    count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TextMiningResult(term={self.term}, count={self.count})>"