"""
API router for DrugRelationship endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_db
from api.schemas.analytics import (
    DrugRelationshipCreate, DrugRelationshipUpdate, DrugRelationshipResponse, DrugRelationshipList
)
from models.analytics import DrugRelationship
from models.dailymed import Drug

router = APIRouter(
    prefix="/drug-relationships",
    tags=["drug-relationships"],
)


@router.post(
    "/",
    response_model=DrugRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new drug relationship",
    description="Create a new drug relationship with the provided data.",
)
def create_drug_relationship(
    relationship: DrugRelationshipCreate,
    db: Session = Depends(get_db),
):
    """Create a new drug relationship."""
    # Check if source_drug_id exists
    source_drug = db.query(Drug).filter(Drug.id == relationship.source_drug_id).first()
    if source_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source drug with ID {relationship.source_drug_id} not found",
        )
    
    # Check if target_drug_id exists
    target_drug = db.query(Drug).filter(Drug.id == relationship.target_drug_id).first()
    if target_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target drug with ID {relationship.target_drug_id} not found",
        )
    
    db_relationship = DrugRelationship(
        source_drug_id=relationship.source_drug_id,
        target_drug_id=relationship.target_drug_id,
        relationship_type=relationship.relationship_type,
        weight=relationship.weight,
    )
    try:
        db.add(db_relationship)
        db.commit()
        db.refresh(db_relationship)
        return db_relationship
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug relationship with these source and target drugs already exists",
        )


@router.get(
    "/",
    response_model=DrugRelationshipList,
    summary="Get all drug relationships",
    description="Get a list of all drug relationships with pagination.",
)
def read_drug_relationships(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    source_drug_id: Optional[int] = Query(None, description="Filter by source drug ID"),
    target_drug_id: Optional[int] = Query(None, description="Filter by target drug ID"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    db: Session = Depends(get_db),
):
    """Get all drug relationships with optional filtering."""
    query = db.query(DrugRelationship)
    
    # Apply filters if provided
    if source_drug_id is not None:
        query = query.filter(DrugRelationship.source_drug_id == source_drug_id)
    if target_drug_id is not None:
        query = query.filter(DrugRelationship.target_drug_id == target_drug_id)
    if relationship_type:
        query = query.filter(DrugRelationship.relationship_type == relationship_type)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    relationships = query.offset(skip).limit(limit).all()
    
    return {"items": relationships, "total": total}


@router.get(
    "/{source_drug_id}/{target_drug_id}",
    response_model=DrugRelationshipResponse,
    summary="Get a specific drug relationship",
    description="Get a specific drug relationship by its source and target drug IDs.",
)
def read_drug_relationship(
    source_drug_id: int,
    target_drug_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific drug relationship by source and target drug IDs."""
    relationship = db.query(DrugRelationship).filter(
        DrugRelationship.source_drug_id == source_drug_id,
        DrugRelationship.target_drug_id == target_drug_id,
    ).first()
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug relationship with source drug ID {source_drug_id} and target drug ID {target_drug_id} not found",
        )
    return relationship


@router.put(
    "/{source_drug_id}/{target_drug_id}",
    response_model=DrugRelationshipResponse,
    summary="Update a drug relationship",
    description="Update a drug relationship with the provided data.",
)
def update_drug_relationship(
    source_drug_id: int,
    target_drug_id: int,
    relationship_update: DrugRelationshipUpdate,
    db: Session = Depends(get_db),
):
    """Update a drug relationship."""
    db_relationship = db.query(DrugRelationship).filter(
        DrugRelationship.source_drug_id == source_drug_id,
        DrugRelationship.target_drug_id == target_drug_id,
    ).first()
    if db_relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug relationship with source drug ID {source_drug_id} and target drug ID {target_drug_id} not found",
        )
    
    # Update fields if provided
    update_data = relationship_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_relationship, key, value)
    
    db.commit()
    db.refresh(db_relationship)
    return db_relationship


@router.delete(
    "/{source_drug_id}/{target_drug_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drug relationship",
    description="Delete a drug relationship by its source and target drug IDs.",
)
def delete_drug_relationship(
    source_drug_id: int,
    target_drug_id: int,
    db: Session = Depends(get_db),
):
    """Delete a drug relationship."""
    db_relationship = db.query(DrugRelationship).filter(
        DrugRelationship.source_drug_id == source_drug_id,
        DrugRelationship.target_drug_id == target_drug_id,
    ).first()
    if db_relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug relationship with source drug ID {source_drug_id} and target drug ID {target_drug_id} not found",
        )
    
    db.delete(db_relationship)
    db.commit()
    return None
