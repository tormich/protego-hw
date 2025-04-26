"""
Pydantic schemas for DrugClass model.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl


class DrugClassBase(BaseModel):
    """Base schema for DrugClass."""
    name: str = Field(..., description="The name of the drug class", example="Antibiotics")
    url: HttpUrl = Field(..., description="The URL to the drug class page", 
                         example="https://dailymed.nlm.nih.gov/dailymed/drugClass.cfm?class_id=123")
    analyzed: Optional[bool] = Field(False, description="Whether this drug class has been analyzed")


class DrugClassCreate(DrugClassBase):
    """Schema for creating a new DrugClass."""
    pass


class DrugClassUpdate(BaseModel):
    """Schema for updating a DrugClass."""
    name: Optional[str] = Field(None, description="The name of the drug class")
    url: Optional[HttpUrl] = Field(None, description="The URL to the drug class page")
    analyzed: Optional[bool] = Field(None, description="Whether this drug class has been analyzed")


class DrugClassInDB(DrugClassBase):
    """Schema for DrugClass as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class DrugClassResponse(DrugClassInDB):
    """Schema for DrugClass response."""
    pass


class DrugClassList(BaseModel):
    """Schema for a list of DrugClass objects."""
    items: List[DrugClassResponse]
    total: int
