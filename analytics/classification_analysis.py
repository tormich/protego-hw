"""
Drug classification analysis module.

This module provides functionality for analyzing drug classifications.
"""

import logging
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict

from sqlalchemy import func, distinct, and_, or_

from models.dailymed import Drug, DrugClass
from models.analytics import DrugClassAnalysis, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class ClassificationAnalyzer(BaseAnalyzer):
    """Analyzer for drug classifications."""

    def analyze(self) -> Dict[str, Any]:
        """Analyze drug classifications.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting drug classification analysis")
        
        # Initialize results dictionary
        results = {
            "class_distribution": {},
            "cross_classification": [],
            "class_hierarchy": {},
            "summary": {
                "total_drug_classes": 0,
                "total_drugs": 0,
                "drugs_with_class": 0,
                "drugs_without_class": 0,
                "avg_drugs_per_class": 0,
            }
        }
        
        # Get all drug classes
        drug_classes = self.db.query(DrugClass).all()
        results["summary"]["total_drug_classes"] = len(drug_classes)
        
        # Get total drugs count
        total_drugs = self.db.query(func.count(Drug.id)).scalar()
        results["summary"]["total_drugs"] = total_drugs
        
        # Get drugs without class
        drugs_without_class = self.db.query(func.count(Drug.id)).filter(Drug.drug_class_id.is_(None)).scalar()
        results["summary"]["drugs_without_class"] = drugs_without_class
        results["summary"]["drugs_with_class"] = total_drugs - drugs_without_class
        
        # Calculate drug count per class
        class_drug_counts = {}
        for drug_class in drug_classes:
            drug_count = self.db.query(func.count(Drug.id)).filter(Drug.drug_class_id == drug_class.id).scalar()
            class_drug_counts[drug_class.id] = drug_count
            
            results["class_distribution"][drug_class.name] = {
                "id": drug_class.id,
                "drug_count": drug_count,
                "url": drug_class.url
            }
        
        # Calculate average drugs per class
        if results["summary"]["total_drug_classes"] > 0:
            results["summary"]["avg_drugs_per_class"] = (
                results["summary"]["drugs_with_class"] / results["summary"]["total_drug_classes"]
            )
        
        # Identify potential cross-classification by looking for similar drug names across classes
        # This is a simplified approach - in a real system, we might use more sophisticated methods
        drug_name_to_classes = defaultdict(set)
        
        # Get all drugs with their names and class IDs
        drugs = self.db.query(Drug.name, Drug.drug_class_id).filter(Drug.drug_class_id.isnot(None)).all()
        
        for drug_name, class_id in drugs:
            # Normalize drug name (remove dosage info, etc.)
            normalized_name = drug_name.split()[0].lower()
            drug_name_to_classes[normalized_name].add(class_id)
        
        # Find drugs that appear in multiple classes
        for drug_name, class_ids in drug_name_to_classes.items():
            if len(class_ids) > 1:
                class_names = [
                    self.db.query(DrugClass.name).filter(DrugClass.id == class_id).scalar()
                    for class_id in class_ids
                ]
                
                results["cross_classification"].append({
                    "drug_name": drug_name,
                    "class_ids": list(class_ids),
                    "class_names": class_names
                })
        
        # Build a simple class hierarchy based on name patterns
        # This is a simplified approach - in a real system, we might use external ontologies
        class_hierarchy = defaultdict(list)
        
        for drug_class in drug_classes:
            # Split class name by common separators
            parts = drug_class.name.split('/')
            
            if len(parts) > 1:
                # If the name has multiple parts, consider the first part as parent
                parent = parts[0].strip()
                child = drug_class.name
                
                class_hierarchy[parent].append({
                    "id": drug_class.id,
                    "name": child,
                    "drug_count": class_drug_counts.get(drug_class.id, 0)
                })
        
        results["class_hierarchy"] = dict(class_hierarchy)
        
        logger.info(f"Completed drug classification analysis. Found {len(drug_classes)} drug classes.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving drug classification analysis results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="ClassificationAnalyzer",
            result_type="classification_analysis",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save individual drug class analysis
        for class_name, class_data in results["class_distribution"].items():
            class_id = class_data["id"]
            drug_count = class_data["drug_count"]
            
            # Count how many times this class appears in cross-classification
            cross_class_count = sum(
                1 for item in results["cross_classification"] if class_id in item["class_ids"]
            )
            
            # Create or update drug class analysis record
            class_analysis = self.db.query(DrugClassAnalysis).filter(
                DrugClassAnalysis.drug_class_id == class_id
            ).first()
            
            if class_analysis:
                # Update existing record
                class_analysis.drug_count = drug_count
                class_analysis.cross_classification_count = cross_class_count
            else:
                # Create new record
                class_analysis = DrugClassAnalysis(
                    drug_class_id=class_id,
                    drug_count=drug_count,
                    cross_classification_count=cross_class_count
                )
                self.db.add(class_analysis)
        
        # Commit changes
        self.db.commit()
        
        logger.info(f"Saved drug classification analysis results for {len(results['class_distribution'])} drug classes")
