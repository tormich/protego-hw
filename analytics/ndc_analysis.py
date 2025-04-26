"""
NDC code analysis module.

This module provides functionality for analyzing NDC codes in drug data.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Set

from sqlalchemy import func, distinct, and_, or_

from models.dailymed import Drug
from models.analytics import NDCAnalysis, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class NDCAnalyzer(BaseAnalyzer):
    """Analyzer for NDC codes."""

    def analyze(self) -> Dict[str, Any]:
        """Analyze NDC codes.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting NDC code analysis")
        
        # Initialize results dictionary
        results = {
            "ndc_distribution": {},
            "shared_codes": [],
            "manufacturer_patterns": {},
            "summary": {
                "total_ndc_codes": 0,
                "unique_ndc_codes": 0,
                "shared_ndc_codes": 0,
                "drugs_with_ndc": 0,
                "drugs_without_ndc": 0,
                "avg_ndc_per_drug": 0,
            }
        }
        
        # Get all drugs with NDC codes
        drugs_with_ndc = self.db.query(Drug).filter(Drug.ndc_codes.isnot(None)).all()
        drugs_without_ndc = self.db.query(func.count(Drug.id)).filter(
            or_(Drug.ndc_codes.is_(None), func.array_length(Drug.ndc_codes, 1) == 0)
        ).scalar()
        
        # Update summary stats
        results["summary"]["drugs_with_ndc"] = len(drugs_with_ndc)
        results["summary"]["drugs_without_ndc"] = drugs_without_ndc
        
        # Process NDC codes
        all_ndc_codes = set()
        ndc_to_drugs = {}
        
        for drug in drugs_with_ndc:
            if not drug.ndc_codes:
                continue
                
            for ndc in drug.ndc_codes:
                all_ndc_codes.add(ndc)
                
                # Count drugs per NDC code
                if ndc not in ndc_to_drugs:
                    ndc_to_drugs[ndc] = []
                ndc_to_drugs[ndc].append(drug.id)
        
        # Calculate NDC distribution
        for ndc, drug_ids in ndc_to_drugs.items():
            drug_count = len(drug_ids)
            results["ndc_distribution"][ndc] = drug_count
            
            # Identify shared NDC codes
            if drug_count > 1:
                results["shared_codes"].append({
                    "ndc_code": ndc,
                    "drug_count": drug_count,
                    "drug_ids": drug_ids
                })
        
        # Extract manufacturer prefixes (first segment of NDC code)
        manufacturer_prefixes = {}
        for ndc in all_ndc_codes:
            # NDC codes can be in different formats (e.g., 5-4-2, 5-3-2, etc.)
            # We'll try to extract the first segment (manufacturer code)
            prefix = ndc.split('-')[0] if '-' in ndc else ndc.split(' ')[0]
            
            if prefix not in manufacturer_prefixes:
                manufacturer_prefixes[prefix] = 0
            manufacturer_prefixes[prefix] += 1
        
        results["manufacturer_patterns"] = manufacturer_prefixes
        
        # Update summary statistics
        results["summary"]["total_ndc_codes"] = len(all_ndc_codes)
        results["summary"]["unique_ndc_codes"] = len([k for k, v in ndc_to_drugs.items() if len(v) == 1])
        results["summary"]["shared_ndc_codes"] = len([k for k, v in ndc_to_drugs.items() if len(v) > 1])
        
        if results["summary"]["drugs_with_ndc"] > 0:
            results["summary"]["avg_ndc_per_drug"] = len(all_ndc_codes) / results["summary"]["drugs_with_ndc"]
        
        logger.info(f"Completed NDC code analysis. Found {len(all_ndc_codes)} NDC codes across {len(drugs_with_ndc)} drugs.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving NDC analysis results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="NDCAnalyzer",
            result_type="ndc_analysis",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save individual NDC code analysis
        for ndc, drug_count in results["ndc_distribution"].items():
            # Check if this NDC code is shared across multiple drugs
            is_shared = 1 if drug_count > 1 else 0
            
            # Extract manufacturer prefix
            prefix = ndc.split('-')[0] if '-' in ndc else ndc.split(' ')[0]
            
            # Create or update NDC analysis record
            ndc_analysis = self.db.query(NDCAnalysis).filter(NDCAnalysis.ndc_code == ndc).first()
            
            if ndc_analysis:
                # Update existing record
                ndc_analysis.drug_count = drug_count
                ndc_analysis.is_shared = is_shared
                ndc_analysis.manufacturer_prefix = prefix
            else:
                # Create new record
                ndc_analysis = NDCAnalysis(
                    ndc_code=ndc,
                    drug_count=drug_count,
                    is_shared=is_shared,
                    manufacturer_prefix=prefix
                )
                self.db.add(ndc_analysis)
        
        # Commit changes
        self.db.commit()
        
        logger.info(f"Saved NDC analysis results for {len(results['ndc_distribution'])} NDC codes")
