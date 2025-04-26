"""
API router for DrugClass endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_db
from api.schemas.drug_class import (
    DrugClassCreate, DrugClassUpdate, DrugClassResponse, DrugClassList
)
from models.dailymed import DrugClass

router = APIRouter(
    prefix="/drug-classes",
    tags=["drug-classes"],
)


@router.post(
    "/",
    response_model=DrugClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new drug class",
    description="Create a new drug class with the provided data.",
)
def create_drug_class(
    drug_class: DrugClassCreate,
    db: Session = Depends(get_db),
):
    """Create a new drug class."""
    db_drug_class = DrugClass(
        name=drug_class.name,
        url=str(drug_class.url),
        analyzed=drug_class.analyzed,
    )
    try:
        db.add(db_drug_class)
        db.commit()
        db.refresh(db_drug_class)
        return db_drug_class
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug class with this name or URL already exists",
        )


@router.get(
    "/",
    response_model=DrugClassList,
    summary="Get all drug classes",
    description="Get a list of all drug classes with pagination.",
)
def read_drug_classes(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    name: Optional[str] = Query(None, description="Filter by name (case-insensitive, partial match)"),
    analyzed: Optional[bool] = Query(None, description="Filter by analyzed status"),
    db: Session = Depends(get_db),
):
    """Get all drug classes with optional filtering."""
    query = db.query(DrugClass)
    
    # Apply filters if provided
    if name:
        query = query.filter(DrugClass.name.ilike(f"%{name}%"))
    if analyzed is not None:
        query = query.filter(DrugClass.analyzed == analyzed)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    drug_classes = query.offset(skip).limit(limit).all()
    
    return {"items": drug_classes, "total": total}


@router.get(
    "/{drug_class_id}",
    response_model=DrugClassResponse,
    summary="Get a specific drug class",
    description="Get a specific drug class by its ID.",
)
def read_drug_class(
    drug_class_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific drug class by ID."""
    drug_class = db.query(DrugClass).filter(DrugClass.id == drug_class_id).first()
    if drug_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class with ID {drug_class_id} not found",
        )
    return drug_class


@router.put(
    "/{drug_class_id}",
    response_model=DrugClassResponse,
    summary="Update a drug class",
    description="Update a drug class with the provided data.",
)
def update_drug_class(
    drug_class_id: int,
    drug_class_update: DrugClassUpdate,
    db: Session = Depends(get_db),
):
    """Update a drug class."""
    db_drug_class = db.query(DrugClass).filter(DrugClass.id == drug_class_id).first()
    if db_drug_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class with ID {drug_class_id} not found",
        )
    
    # Update fields if provided
    update_data = drug_class_update.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
    
    for key, value in update_data.items():
        setattr(db_drug_class, key, value)
    
    try:
        db.commit()
        db.refresh(db_drug_class)
        return db_drug_class
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug class with this name or URL already exists",
        )


@router.delete(
    "/{drug_class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drug class",
    description="Delete a drug class by its ID.",
)
def delete_drug_class(
    drug_class_id: int,
    db: Session = Depends(get_db),
):
    """Delete a drug class."""
    db_drug_class = db.query(DrugClass).filter(DrugClass.id == drug_class_id).first()
    if db_drug_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class with ID {drug_class_id} not found",
        )
    
    db.delete(db_drug_class)
    db.commit()
    return None
