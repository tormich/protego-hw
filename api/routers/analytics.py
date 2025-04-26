"""
API router for analytics endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_db
from api.schemas.analytics import (
    AnalyticsResultCreate, AnalyticsResultUpdate, AnalyticsResultResponse, AnalyticsResultList,
    NDCAnalysisCreate, NDCAnalysisUpdate, NDCAnalysisResponse, NDCAnalysisList,
    DrugClassAnalysisCreate, DrugClassAnalysisUpdate, DrugClassAnalysisResponse, DrugClassAnalysisList,
    NameAnalysisCreate, NameAnalysisUpdate, NameAnalysisResponse, NameAnalysisList,
)
from models.analytics import (
    AnalyticsResult, NDCAnalysis, DrugClassAnalysis, NameAnalysis
)
from models.dailymed import DrugClass

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


# AnalyticsResult endpoints
@router.post(
    "/results",
    response_model=AnalyticsResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new analytics result",
    description="Create a new analytics result with the provided data.",
)
def create_analytics_result(
    result: AnalyticsResultCreate,
    db: Session = Depends(get_db),
):
    """Create a new analytics result."""
    db_result = AnalyticsResult(
        analyzer_name=result.analyzer_name,
        result_type=result.result_type,
        result_data=result.result_data,
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


@router.get(
    "/results",
    response_model=AnalyticsResultList,
    summary="Get all analytics results",
    description="Get a list of all analytics results with pagination.",
)
def read_analytics_results(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    analyzer_name: Optional[str] = Query(None, description="Filter by analyzer name"),
    result_type: Optional[str] = Query(None, description="Filter by result type"),
    db: Session = Depends(get_db),
):
    """Get all analytics results with optional filtering."""
    query = db.query(AnalyticsResult)
    
    # Apply filters if provided
    if analyzer_name:
        query = query.filter(AnalyticsResult.analyzer_name == analyzer_name)
    if result_type:
        query = query.filter(AnalyticsResult.result_type == result_type)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    results = query.offset(skip).limit(limit).all()
    
    return {"items": results, "total": total}


@router.get(
    "/results/{result_id}",
    response_model=AnalyticsResultResponse,
    summary="Get a specific analytics result",
    description="Get a specific analytics result by its ID.",
)
def read_analytics_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific analytics result by ID."""
    result = db.query(AnalyticsResult).filter(AnalyticsResult.id == result_id).first()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics result with ID {result_id} not found",
        )
    return result


@router.put(
    "/results/{result_id}",
    response_model=AnalyticsResultResponse,
    summary="Update an analytics result",
    description="Update an analytics result with the provided data.",
)
def update_analytics_result(
    result_id: int,
    result_update: AnalyticsResultUpdate,
    db: Session = Depends(get_db),
):
    """Update an analytics result."""
    db_result = db.query(AnalyticsResult).filter(AnalyticsResult.id == result_id).first()
    if db_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics result with ID {result_id} not found",
        )
    
    # Update fields if provided
    update_data = result_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_result, key, value)
    
    db.commit()
    db.refresh(db_result)
    return db_result


@router.delete(
    "/results/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an analytics result",
    description="Delete an analytics result by its ID.",
)
def delete_analytics_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """Delete an analytics result."""
    db_result = db.query(AnalyticsResult).filter(AnalyticsResult.id == result_id).first()
    if db_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics result with ID {result_id} not found",
        )
    
    db.delete(db_result)
    db.commit()
    return None


# NDCAnalysis endpoints
@router.post(
    "/ndc",
    response_model=NDCAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new NDC analysis",
    description="Create a new NDC analysis with the provided data.",
)
def create_ndc_analysis(
    analysis: NDCAnalysisCreate,
    db: Session = Depends(get_db),
):
    """Create a new NDC analysis."""
    db_analysis = NDCAnalysis(
        ndc_code=analysis.ndc_code,
        drug_count=analysis.drug_count,
        is_shared=analysis.is_shared,
        manufacturer_prefix=analysis.manufacturer_prefix,
    )
    try:
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        return db_analysis
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NDC analysis with this NDC code already exists",
        )


@router.get(
    "/ndc",
    response_model=NDCAnalysisList,
    summary="Get all NDC analyses",
    description="Get a list of all NDC analyses with pagination.",
)
def read_ndc_analyses(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    ndc_code: Optional[str] = Query(None, description="Filter by NDC code (partial match)"),
    is_shared: Optional[int] = Query(None, description="Filter by shared status (0=unique, 1=shared)"),
    db: Session = Depends(get_db),
):
    """Get all NDC analyses with optional filtering."""
    query = db.query(NDCAnalysis)
    
    # Apply filters if provided
    if ndc_code:
        query = query.filter(NDCAnalysis.ndc_code.ilike(f"%{ndc_code}%"))
    if is_shared is not None:
        query = query.filter(NDCAnalysis.is_shared == is_shared)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    analyses = query.offset(skip).limit(limit).all()
    
    return {"items": analyses, "total": total}


@router.get(
    "/ndc/{analysis_id}",
    response_model=NDCAnalysisResponse,
    summary="Get a specific NDC analysis",
    description="Get a specific NDC analysis by its ID.",
)
def read_ndc_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific NDC analysis by ID."""
    analysis = db.query(NDCAnalysis).filter(NDCAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NDC analysis with ID {analysis_id} not found",
        )
    return analysis


@router.put(
    "/ndc/{analysis_id}",
    response_model=NDCAnalysisResponse,
    summary="Update an NDC analysis",
    description="Update an NDC analysis with the provided data.",
)
def update_ndc_analysis(
    analysis_id: int,
    analysis_update: NDCAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """Update an NDC analysis."""
    db_analysis = db.query(NDCAnalysis).filter(NDCAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NDC analysis with ID {analysis_id} not found",
        )
    
    # Update fields if provided
    update_data = analysis_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_analysis, key, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


@router.delete(
    "/ndc/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an NDC analysis",
    description="Delete an NDC analysis by its ID.",
)
def delete_ndc_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Delete an NDC analysis."""
    db_analysis = db.query(NDCAnalysis).filter(NDCAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NDC analysis with ID {analysis_id} not found",
        )
    
    db.delete(db_analysis)
    db.commit()
    return None


# DrugClassAnalysis endpoints
@router.post(
    "/drug-classes",
    response_model=DrugClassAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new drug class analysis",
    description="Create a new drug class analysis with the provided data.",
)
def create_drug_class_analysis(
    analysis: DrugClassAnalysisCreate,
    db: Session = Depends(get_db),
):
    """Create a new drug class analysis."""
    # Check if drug_class_id exists
    drug_class = db.query(DrugClass).filter(DrugClass.id == analysis.drug_class_id).first()
    if drug_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class with ID {analysis.drug_class_id} not found",
        )
    
    db_analysis = DrugClassAnalysis(
        drug_class_id=analysis.drug_class_id,
        drug_count=analysis.drug_count,
        cross_classification_count=analysis.cross_classification_count,
    )
    try:
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        return db_analysis
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drug class analysis with this drug class ID already exists",
        )


@router.get(
    "/drug-classes",
    response_model=DrugClassAnalysisList,
    summary="Get all drug class analyses",
    description="Get a list of all drug class analyses with pagination.",
)
def read_drug_class_analyses(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    drug_class_id: Optional[int] = Query(None, description="Filter by drug class ID"),
    db: Session = Depends(get_db),
):
    """Get all drug class analyses with optional filtering."""
    query = db.query(DrugClassAnalysis)
    
    # Apply filters if provided
    if drug_class_id is not None:
        query = query.filter(DrugClassAnalysis.drug_class_id == drug_class_id)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    analyses = query.offset(skip).limit(limit).all()
    
    return {"items": analyses, "total": total}


@router.get(
    "/drug-classes/{analysis_id}",
    response_model=DrugClassAnalysisResponse,
    summary="Get a specific drug class analysis",
    description="Get a specific drug class analysis by its ID.",
)
def read_drug_class_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific drug class analysis by ID."""
    analysis = db.query(DrugClassAnalysis).filter(DrugClassAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class analysis with ID {analysis_id} not found",
        )
    return analysis


@router.put(
    "/drug-classes/{analysis_id}",
    response_model=DrugClassAnalysisResponse,
    summary="Update a drug class analysis",
    description="Update a drug class analysis with the provided data.",
)
def update_drug_class_analysis(
    analysis_id: int,
    analysis_update: DrugClassAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """Update a drug class analysis."""
    db_analysis = db.query(DrugClassAnalysis).filter(DrugClassAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class analysis with ID {analysis_id} not found",
        )
    
    # Update fields if provided
    update_data = analysis_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_analysis, key, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


@router.delete(
    "/drug-classes/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drug class analysis",
    description="Delete a drug class analysis by its ID.",
)
def delete_drug_class_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Delete a drug class analysis."""
    db_analysis = db.query(DrugClassAnalysis).filter(DrugClassAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug class analysis with ID {analysis_id} not found",
        )
    
    db.delete(db_analysis)
    db.commit()
    return None


# NameAnalysis endpoints
@router.post(
    "/names",
    response_model=NameAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new name analysis",
    description="Create a new name analysis with the provided data.",
)
def create_name_analysis(
    analysis: NameAnalysisCreate,
    db: Session = Depends(get_db),
):
    """Create a new name analysis."""
    db_analysis = NameAnalysis(
        pattern_type=analysis.pattern_type,
        pattern=analysis.pattern,
        count=analysis.count,
        is_brand=analysis.is_brand,
        avg_length=analysis.avg_length,
    )
    try:
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        return db_analysis
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Name analysis with this pattern type and pattern already exists",
        )


@router.get(
    "/names",
    response_model=NameAnalysisList,
    summary="Get all name analyses",
    description="Get a list of all name analyses with pagination.",
)
def read_name_analyses(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type (prefix, suffix, full)"),
    pattern: Optional[str] = Query(None, description="Filter by pattern (partial match)"),
    is_brand: Optional[int] = Query(None, description="Filter by brand status (0=generic, 1=brand)"),
    db: Session = Depends(get_db),
):
    """Get all name analyses with optional filtering."""
    query = db.query(NameAnalysis)
    
    # Apply filters if provided
    if pattern_type:
        query = query.filter(NameAnalysis.pattern_type == pattern_type)
    if pattern:
        query = query.filter(NameAnalysis.pattern.ilike(f"%{pattern}%"))
    if is_brand is not None:
        query = query.filter(NameAnalysis.is_brand == is_brand)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    analyses = query.offset(skip).limit(limit).all()
    
    return {"items": analyses, "total": total}


@router.get(
    "/names/{analysis_id}",
    response_model=NameAnalysisResponse,
    summary="Get a specific name analysis",
    description="Get a specific name analysis by its ID.",
)
def read_name_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific name analysis by ID."""
    analysis = db.query(NameAnalysis).filter(NameAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name analysis with ID {analysis_id} not found",
        )
    return analysis


@router.put(
    "/names/{analysis_id}",
    response_model=NameAnalysisResponse,
    summary="Update a name analysis",
    description="Update a name analysis with the provided data.",
)
def update_name_analysis(
    analysis_id: int,
    analysis_update: NameAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """Update a name analysis."""
    db_analysis = db.query(NameAnalysis).filter(NameAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name analysis with ID {analysis_id} not found",
        )
    
    # Update fields if provided
    update_data = analysis_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_analysis, key, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


@router.delete(
    "/names/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a name analysis",
    description="Delete a name analysis by its ID.",
)
def delete_name_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """Delete a name analysis."""
    db_analysis = db.query(NameAnalysis).filter(NameAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name analysis with ID {analysis_id} not found",
        )
    
    db.delete(db_analysis)
    db.commit()
    return None
