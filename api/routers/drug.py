"""
API router for Drug endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_db
from api.schemas.drug import DrugCreate, DrugUpdate, DrugResponse, DrugList
from models.dailymed import Drug, DrugClass

router = APIRouter(
    prefix="/drugs",
    tags=["drugs"],
)


@router.post(
    "/",
    response_model=DrugResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new drug",
    description="Create a new drug with the provided data.",
)
def create_drug(
    drug: DrugCreate,
    db: Session = Depends(get_db),
):
    """Create a new drug."""
    # Check if drug_class_id exists if provided
    if drug.drug_class_id is not None:
        drug_class = db.query(DrugClass).filter(DrugClass.id == drug.drug_class_id).first()
        if drug_class is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drug class with ID {drug.drug_class_id} not found",
            )
    
    db_drug = Drug(
        name=drug.name,
        url=str(drug.url),
        ndc_codes=drug.ndc_codes,
        drug_class_id=drug.drug_class_id,
    )
    try:
        db.add(db_drug)
        db.commit()
        db.refresh(db_drug)
        return db_drug
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug with this name or URL already exists",
        )


@router.get(
    "/",
    response_model=DrugList,
    summary="Get all drugs",
    description="Get a list of all drugs with pagination.",
)
def read_drugs(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    name: Optional[str] = Query(None, description="Filter by name (case-insensitive, partial match)"),
    drug_class_id: Optional[int] = Query(None, description="Filter by drug class ID"),
    ndc_code: Optional[str] = Query(None, description="Filter by NDC code (exact match)"),
    db: Session = Depends(get_db),
):
    """Get all drugs with optional filtering."""
    query = db.query(Drug)
    
    # Apply filters if provided
    if name:
        query = query.filter(Drug.name.ilike(f"%{name}%"))
    if drug_class_id is not None:
        query = query.filter(Drug.drug_class_id == drug_class_id)
    if ndc_code:
        query = query.filter(Drug.ndc_codes.any(ndc_code))
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    drugs = query.offset(skip).limit(limit).all()
    
    return {"items": drugs, "total": total}


@router.get(
    "/{drug_id}",
    response_model=DrugResponse,
    summary="Get a specific drug",
    description="Get a specific drug by its ID.",
)
def read_drug(
    drug_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific drug by ID."""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug with ID {drug_id} not found",
        )
    return drug


@router.put(
    "/{drug_id}",
    response_model=DrugResponse,
    summary="Update a drug",
    description="Update a drug with the provided data.",
)
def update_drug(
    drug_id: int,
    drug_update: DrugUpdate,
    db: Session = Depends(get_db),
):
    """Update a drug."""
    db_drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if db_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug with ID {drug_id} not found",
        )
    
    # Check if drug_class_id exists if provided
    if drug_update.drug_class_id is not None:
        drug_class = db.query(DrugClass).filter(DrugClass.id == drug_update.drug_class_id).first()
        if drug_class is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drug class with ID {drug_update.drug_class_id} not found",
            )
    
    # Update fields if provided
    update_data = drug_update.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
    
    for key, value in update_data.items():
        setattr(db_drug, key, value)
    
    try:
        db.commit()
        db.refresh(db_drug)
        return db_drug
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug with this name or URL already exists",
        )


@router.delete(
    "/{drug_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drug",
    description="Delete a drug by its ID.",
)
def delete_drug(
    drug_id: int,
    db: Session = Depends(get_db),
):
    """Delete a drug."""
    db_drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if db_drug is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug with ID {drug_id} not found",
        )
    
    db.delete(db_drug)
    db.commit()
    return None
