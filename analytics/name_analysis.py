"""
Drug name analysis module.

This module provides functionality for analyzing drug names.
"""

import logging
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter

from sqlalchemy import func, distinct, and_, or_

from models.dailymed import Drug
from models.analytics import NameAnalysis, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class NameAnalyzer(BaseAnalyzer):
    """Analyzer for drug names."""

    # Common brand name suffixes and prefixes
    BRAND_INDICATORS = [
        'XR', 'SR', 'ER', 'XL', 'CR', 'DR', 'LA', 'IR',  # Extended/sustained release
        'HCT', 'Plus', 'Forte', 'Extra',  # Strength indicators
        'Pediatric', 'Junior', 'Adult',  # Age-specific
    ]
    
    # Common generic name suffixes
    GENERIC_SUFFIXES = [
        'ine', 'ol', 'ide', 'ate', 'ium', 'ic', 'in', 'il', 'en',
        'one', 'an', 'cin', 'mycin', 'micin', 'oxacin', 'profen', 'statin',
        'pril', 'sartan', 'dipine', 'zepam', 'zolam', 'azepam', 'azolam',
        'tidine', 'dronate', 'parib', 'tinib', 'ciclib', 'rafenib', 'metinib',
    ]

    def analyze(self) -> Dict[str, Any]:
        """Analyze drug names.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting drug name analysis")
        
        # Initialize results dictionary
        results = {
            "common_prefixes": {},
            "common_suffixes": {},
            "brand_vs_generic": {
                "brand": 0,
                "generic": 0,
                "unknown": 0,
                "examples": {
                    "brand": [],
                    "generic": []
                }
            },
            "name_length": {
                "distribution": {},
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0,
            },
            "summary": {
                "total_drugs": 0,
            }
        }
        
        # Get all drugs
        drugs = self.db.query(Drug).all()
        results["summary"]["total_drugs"] = len(drugs)
        
        # Process drug names
        all_prefixes = []
        all_suffixes = []
        name_lengths = []
        brand_count = 0
        generic_count = 0
        unknown_count = 0
        
        for drug in drugs:
            # Skip drugs without names
            if not drug.name:
                continue
                
            # Clean and normalize the name
            name = drug.name.strip()
            name_parts = name.split()
            
            # Extract the first word (main name)
            main_name = name_parts[0] if name_parts else ""
            
            # Skip empty names
            if not main_name:
                continue
                
            # Calculate name length
            name_length = len(main_name)
            name_lengths.append(name_length)
            
            # Extract prefix (first 3 letters)
            if len(main_name) >= 3:
                prefix = main_name[:3].lower()
                all_prefixes.append(prefix)
            
            # Extract suffix (last 3 letters)
            if len(main_name) >= 3:
                suffix = main_name[-3:].lower()
                all_suffixes.append(suffix)
            
            # Classify as brand or generic
            is_brand = self._is_likely_brand(name)
            is_generic = self._is_likely_generic(name)
            
            if is_brand and not is_generic:
                brand_count += 1
                if len(results["brand_vs_generic"]["examples"]["brand"]) < 5:
                    results["brand_vs_generic"]["examples"]["brand"].append(name)
            elif is_generic and not is_brand:
                generic_count += 1
                if len(results["brand_vs_generic"]["examples"]["generic"]) < 5:
                    results["brand_vs_generic"]["examples"]["generic"].append(name)
            else:
                unknown_count += 1
        
        # Calculate prefix and suffix frequencies
        prefix_counter = Counter(all_prefixes)
        suffix_counter = Counter(all_suffixes)
        
        # Get the top 20 prefixes and suffixes
        results["common_prefixes"] = dict(prefix_counter.most_common(20))
        results["common_suffixes"] = dict(suffix_counter.most_common(20))
        
        # Update brand vs generic counts
        results["brand_vs_generic"]["brand"] = brand_count
        results["brand_vs_generic"]["generic"] = generic_count
        results["brand_vs_generic"]["unknown"] = unknown_count
        
        # Calculate name length statistics
        if name_lengths:
            results["name_length"]["avg_length"] = sum(name_lengths) / len(name_lengths)
            results["name_length"]["min_length"] = min(name_lengths)
            results["name_length"]["max_length"] = max(name_lengths)
            
            # Create length distribution
            length_counter = Counter(name_lengths)
            results["name_length"]["distribution"] = dict(sorted(length_counter.items()))
        
        logger.info(f"Completed drug name analysis. Processed {len(drugs)} drug names.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving drug name analysis results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="NameAnalyzer",
            result_type="name_analysis",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save prefix analysis
        for prefix, count in results["common_prefixes"].items():
            name_analysis = self.db.query(NameAnalysis).filter(
                and_(NameAnalysis.pattern == prefix, NameAnalysis.pattern_type == 'prefix')
            ).first()
            
            if name_analysis:
                name_analysis.count = count
            else:
                name_analysis = NameAnalysis(
                    pattern_type='prefix',
                    pattern=prefix,
                    count=count
                )
                self.db.add(name_analysis)
        
        # Save suffix analysis
        for suffix, count in results["common_suffixes"].items():
            name_analysis = self.db.query(NameAnalysis).filter(
                and_(NameAnalysis.pattern == suffix, NameAnalysis.pattern_type == 'suffix')
            ).first()
            
            if name_analysis:
                name_analysis.count = count
            else:
                name_analysis = NameAnalysis(
                    pattern_type='suffix',
                    pattern=suffix,
                    count=count
                )
                self.db.add(name_analysis)
        
        # Save brand/generic indicators
        for indicator in self.BRAND_INDICATORS:
            name_analysis = self.db.query(NameAnalysis).filter(
                and_(NameAnalysis.pattern == indicator.lower(), NameAnalysis.pattern_type == 'indicator')
            ).first()
            
            if not name_analysis:
                name_analysis = NameAnalysis(
                    pattern_type='indicator',
                    pattern=indicator.lower(),
                    is_brand=1,
                    count=0  # We'll update this in a real implementation
                )
                self.db.add(name_analysis)
        
        for suffix in self.GENERIC_SUFFIXES:
            name_analysis = self.db.query(NameAnalysis).filter(
                and_(NameAnalysis.pattern == suffix.lower(), NameAnalysis.pattern_type == 'indicator')
            ).first()
            
            if not name_analysis:
                name_analysis = NameAnalysis(
                    pattern_type='indicator',
                    pattern=suffix.lower(),
                    is_brand=0,  # 0 = generic
                    count=0  # We'll update this in a real implementation
                )
                self.db.add(name_analysis)
        
        # Commit changes
        self.db.commit()
        
        logger.info("Saved drug name analysis results")
    
    def _is_likely_brand(self, name: str) -> bool:
        """Check if a drug name is likely a brand name.
        
        Args:
            name: Drug name to check
            
        Returns:
            bool: True if likely a brand name, False otherwise
        """
        # Brand names often have trademark symbols
        if '®' in name or '™' in name:
            return True
        
        # Check for common brand name indicators
        for indicator in self.BRAND_INDICATORS:
            if indicator in name.split():
                return True
        
        # Brand names often start with a capital letter and don't end with generic suffixes
        if name[0].isupper() and not any(name.lower().endswith(suffix) for suffix in self.GENERIC_SUFFIXES):
            return True
            
        return False
    
    def _is_likely_generic(self, name: str) -> bool:
        """Check if a drug name is likely a generic name.
        
        Args:
            name: Drug name to check
            
        Returns:
            bool: True if likely a generic name, False otherwise
        """
        # Generic names often end with specific suffixes
        for suffix in self.GENERIC_SUFFIXES:
            if name.lower().endswith(suffix):
                return True
                
        # Generic names are usually all lowercase
        if name.islower():
            return True
            
        return False
