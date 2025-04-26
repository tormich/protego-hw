"""
Pydantic schemas for Drug model.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl


class DrugBase(BaseModel):
    """Base schema for Drug."""
    name: str = Field(..., description="The name of the drug", example="Amoxicillin")
    url: HttpUrl = Field(..., description="The URL to the drug page", 
                         example="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=123")
    ndc_codes: Optional[List[str]] = Field(None, description="List of NDC codes for the drug", 
                                          example=["12345-678-90", "12345-678-91"])
    drug_class_id: Optional[int] = Field(None, description="ID of the drug class this drug belongs to")


class DrugCreate(DrugBase):
    """Schema for creating a new Drug."""
    pass


class DrugUpdate(BaseModel):
    """Schema for updating a Drug."""
    name: Optional[str] = Field(None, description="The name of the drug")
    url: Optional[HttpUrl] = Field(None, description="The URL to the drug page")
    ndc_codes: Optional[List[str]] = Field(None, description="List of NDC codes for the drug")
    drug_class_id: Optional[int] = Field(None, description="ID of the drug class this drug belongs to")


class DrugInDB(DrugBase):
    """Schema for Drug as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class DrugResponse(DrugInDB):
    """Schema for Drug response."""
    pass


class DrugList(BaseModel):
    """Schema for a list of Drug objects."""
    items: List[DrugResponse]
    total: int
