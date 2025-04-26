"""
Pydantic schemas for analytics models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field


# Base Analytics Result schemas
class AnalyticsResultBase(BaseModel):
    """Base schema for AnalyticsResult."""
    analyzer_name: str = Field(..., description="Name of the analyzer that produced this result")
    result_type: str = Field(..., description="Type of the result")
    result_data: Dict[str, Any] = Field(..., description="JSON data containing the analysis results")


class AnalyticsResultCreate(AnalyticsResultBase):
    """Schema for creating a new AnalyticsResult."""
    pass


class AnalyticsResultUpdate(BaseModel):
    """Schema for updating an AnalyticsResult."""
    analyzer_name: Optional[str] = Field(None, description="Name of the analyzer that produced this result")
    result_type: Optional[str] = Field(None, description="Type of the result")
    result_data: Optional[Dict[str, Any]] = Field(None, description="JSON data containing the analysis results")


class AnalyticsResultInDB(AnalyticsResultBase):
    """Schema for AnalyticsResult as stored in the database."""
    id: int
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class AnalyticsResultResponse(BaseModel):
    """Schema for AnalyticsResult response.

    All fields are explicitly listed for better readability.
    """
    id: int = Field(..., description="Unique identifier for the analytics result")
    analyzer_name: str = Field(..., description="Name of the analyzer that produced this result")
    result_type: str = Field(..., description="Type of the result")
    result_data: Dict[str, Any] = Field(..., description="JSON data containing the analysis results")
    created_at: datetime = Field(..., description="Timestamp when this result was created")

    class Config:
        """Pydantic config."""
        from_attributes = True


class AnalyticsResultList(BaseModel):
    """Schema for a list of AnalyticsResult objects."""
    items: List[AnalyticsResultResponse]
    total: int


# NDC Analysis schemas
class NDCAnalysisBase(BaseModel):
    """Base schema for NDCAnalysis."""
    ndc_code: str = Field(..., description="NDC code", example="12345-678-90")
    drug_count: int = Field(..., description="Number of drugs with this NDC code")
    is_shared: int = Field(..., description="Whether this NDC code is shared (0=unique, 1=shared)")
    manufacturer_prefix: Optional[str] = Field(None, description="Manufacturer prefix of the NDC code")


class NDCAnalysisCreate(NDCAnalysisBase):
    """Schema for creating a new NDCAnalysis."""
    pass


class NDCAnalysisUpdate(BaseModel):
    """Schema for updating an NDCAnalysis."""
    drug_count: Optional[int] = Field(None, description="Number of drugs with this NDC code")
    is_shared: Optional[int] = Field(None, description="Whether this NDC code is shared (0=unique, 1=shared)")
    manufacturer_prefix: Optional[str] = Field(None, description="Manufacturer prefix of the NDC code")


class NDCAnalysisInDB(NDCAnalysisBase):
    """Schema for NDCAnalysis as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class NDCAnalysisResponse(NDCAnalysisInDB):
    """Schema for NDCAnalysis response."""
    pass


class NDCAnalysisList(BaseModel):
    """Schema for a list of NDCAnalysis objects."""
    items: List[NDCAnalysisResponse]
    total: int


# Drug Class Analysis schemas
class DrugClassAnalysisBase(BaseModel):
    """Base schema for DrugClassAnalysis."""
    drug_class_id: int = Field(..., description="ID of the drug class")
    drug_count: int = Field(..., description="Number of drugs in this class")
    cross_classification_count: int = Field(..., description="Number of drugs that belong to multiple classes")


class DrugClassAnalysisCreate(DrugClassAnalysisBase):
    """Schema for creating a new DrugClassAnalysis."""
    pass


class DrugClassAnalysisUpdate(BaseModel):
    """Schema for updating a DrugClassAnalysis."""
    drug_count: Optional[int] = Field(None, description="Number of drugs in this class")
    cross_classification_count: Optional[int] = Field(None, description="Number of drugs that belong to multiple classes")


class DrugClassAnalysisInDB(DrugClassAnalysisBase):
    """Schema for DrugClassAnalysis as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class DrugClassAnalysisResponse(BaseModel):
    """Schema for DrugClassAnalysis response.

    All fields are explicitly listed for better readability.
    """
    id: int = Field(..., description="Unique identifier for the drug class analysis")
    drug_class_id: int = Field(..., description="ID of the drug class")
    drug_count: int = Field(..., description="Number of drugs in this class")
    cross_classification_count: int = Field(..., description="Number of drugs that belong to multiple classes")
    created_at: datetime = Field(..., description="Timestamp when this analysis was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when this analysis was last updated")

    class Config:
        """Pydantic config."""
        from_attributes = True


class DrugClassAnalysisList(BaseModel):
    """Schema for a list of DrugClassAnalysis objects."""
    items: List[DrugClassAnalysisResponse]
    total: int


# Name Analysis schemas
class NameAnalysisBase(BaseModel):
    """Base schema for NameAnalysis."""
    pattern_type: str = Field(..., description="Type of pattern (prefix, suffix, full)")
    pattern: str = Field(..., description="The pattern")
    count: int = Field(..., description="Number of occurrences")
    is_brand: Optional[int] = Field(None, description="Whether this is a brand name (0=generic, 1=brand, NULL=unknown)")
    avg_length: Optional[float] = Field(None, description="Average length of names with this pattern")


class NameAnalysisCreate(NameAnalysisBase):
    """Schema for creating a new NameAnalysis."""
    pass


class NameAnalysisUpdate(BaseModel):
    """Schema for updating a NameAnalysis."""
    count: Optional[int] = Field(None, description="Number of occurrences")
    is_brand: Optional[int] = Field(None, description="Whether this is a brand name (0=generic, 1=brand, NULL=unknown)")
    avg_length: Optional[float] = Field(None, description="Average length of names with this pattern")


class NameAnalysisInDB(NameAnalysisBase):
    """Schema for NameAnalysis as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class NameAnalysisResponse(BaseModel):
    """Schema for NameAnalysis response.

    All fields are explicitly listed for better readability.
    """
    id: int = Field(..., description="Unique identifier for the name analysis")
    pattern_type: str = Field(..., description="Type of pattern (prefix, suffix, full)")
    pattern: str = Field(..., description="The pattern")
    count: int = Field(..., description="Number of occurrences")
    is_brand: Optional[int] = Field(None, description="Whether this is a brand name (0=generic, 1=brand, NULL=unknown)")
    avg_length: Optional[float] = Field(None, description="Average length of names with this pattern")
    created_at: datetime = Field(..., description="Timestamp when this analysis was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when this analysis was last updated")

    class Config:
        """Pydantic config."""
        from_attributes = True


class NameAnalysisList(BaseModel):
    """Schema for a list of NameAnalysis objects."""
    items: List[NameAnalysisResponse]
    total: int


# Drug Relationship schemas
class DrugRelationshipBase(BaseModel):
    """Base schema for DrugRelationship."""
    source_drug_id: int = Field(..., description="ID of the source drug")
    target_drug_id: int = Field(..., description="ID of the target drug")
    relationship_type: str = Field(..., description="Type of relationship between drugs")
    weight: float = Field(..., description="Weight or strength of the relationship")


class DrugRelationshipCreate(DrugRelationshipBase):
    """Schema for creating a new DrugRelationship."""
    pass


class DrugRelationshipUpdate(BaseModel):
    """Schema for updating a DrugRelationship."""
    relationship_type: Optional[str] = Field(None, description="Type of relationship between drugs")
    weight: Optional[float] = Field(None, description="Weight or strength of the relationship")


class DrugRelationshipResponse(BaseModel):
    """Schema for DrugRelationship response.

    All fields are explicitly listed for better readability.
    """
    source_drug_id: int = Field(..., description="ID of the source drug")
    target_drug_id: int = Field(..., description="ID of the target drug")
    relationship_type: str = Field(..., description="Type of relationship between drugs")
    weight: float = Field(..., description="Weight or strength of the relationship")
    created_at: datetime = Field(..., description="Timestamp when this relationship was created")

    class Config:
        """Pydantic config."""
        from_attributes = True


class DrugRelationshipList(BaseModel):
    """Schema for a list of DrugRelationship objects."""
    items: List[DrugRelationshipResponse]
    total: int
