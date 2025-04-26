"""
Text mining module.

This module provides functionality for text mining on drug data.
"""

import logging
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter

from sqlalchemy import func, distinct, and_, or_

from models.dailymed import Drug, DrugClass
from models.analytics import TextMiningResult, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class TextMiningAnalyzer(BaseAnalyzer):
    """Analyzer for text mining."""

    # Common dosage forms
    DOSAGE_FORMS = [
        'tablet', 'capsule', 'solution', 'injection', 'suspension',
        'cream', 'ointment', 'gel', 'lotion', 'patch', 'spray',
        'syrup', 'powder', 'suppository', 'inhaler', 'drops'
    ]
    
    # Common active ingredients (simplified list)
    COMMON_INGREDIENTS = [
        'acetaminophen', 'ibuprofen', 'aspirin', 'naproxen',
        'amoxicillin', 'azithromycin', 'ciprofloxacin',
        'lisinopril', 'metoprolol', 'atorvastatin', 'simvastatin',
        'metformin', 'insulin', 'levothyroxine', 'albuterol',
        'fluticasone', 'prednisone', 'omeprazole', 'ranitidine'
    ]

    def analyze(self) -> Dict[str, Any]:
        """Analyze text data.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting text mining analysis")
        
        # Initialize results dictionary
        results = {
            "common_terms": {},
            "ingredients": {},
            "dosage_forms": {},
            "summary": {
                "total_drugs": 0,
                "unique_terms": 0,
                "unique_ingredients": 0,
                "unique_dosage_forms": 0,
            }
        }
        
        # Get all drugs
        drugs = self.db.query(Drug).all()
        results["summary"]["total_drugs"] = len(drugs)
        
        # Process drug names
        all_terms = []
        ingredients = []
        dosage_forms = []
        
        for drug in drugs:
            if not drug.name:
                continue
                
            # Extract terms from drug name
            terms = self._extract_terms(drug.name)
            all_terms.extend(terms)
            
            # Extract potential ingredients
            drug_ingredients = self._extract_ingredients(drug.name)
            ingredients.extend(drug_ingredients)
            
            # Extract potential dosage forms
            drug_dosage_forms = self._extract_dosage_forms(drug.name)
            dosage_forms.extend(drug_dosage_forms)
        
        # Calculate term frequencies
        term_counter = Counter(all_terms)
        results["common_terms"] = dict(term_counter.most_common(50))
        
        # Calculate ingredient frequencies
        ingredient_counter = Counter(ingredients)
        results["ingredients"] = dict(ingredient_counter.most_common(20))
        
        # Calculate dosage form frequencies
        dosage_form_counter = Counter(dosage_forms)
        results["dosage_forms"] = dict(dosage_form_counter.most_common(20))
        
        # Update summary statistics
        results["summary"]["unique_terms"] = len(term_counter)
        results["summary"]["unique_ingredients"] = len(ingredient_counter)
        results["summary"]["unique_dosage_forms"] = len(dosage_form_counter)
        
        logger.info(f"Completed text mining analysis. Processed {len(drugs)} drug names.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving text mining results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="TextMiningAnalyzer",
            result_type="text_mining",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save common terms
        for term, count in results["common_terms"].items():
            text_mining_result = self.db.query(TextMiningResult).filter(
                and_(TextMiningResult.term == term, TextMiningResult.term_type == 'term')
            ).first()
            
            if text_mining_result:
                text_mining_result.count = count
            else:
                text_mining_result = TextMiningResult(
                    term=term,
                    term_type='term',
                    count=count
                )
                self.db.add(text_mining_result)
        
        # Save ingredients
        for ingredient, count in results["ingredients"].items():
            text_mining_result = self.db.query(TextMiningResult).filter(
                and_(TextMiningResult.term == ingredient, TextMiningResult.term_type == 'ingredient')
            ).first()
            
            if text_mining_result:
                text_mining_result.count = count
            else:
                text_mining_result = TextMiningResult(
                    term=ingredient,
                    term_type='ingredient',
                    count=count
                )
                self.db.add(text_mining_result)
        
        # Save dosage forms
        for dosage_form, count in results["dosage_forms"].items():
            text_mining_result = self.db.query(TextMiningResult).filter(
                and_(TextMiningResult.term == dosage_form, TextMiningResult.term_type == 'dosage_form')
            ).first()
            
            if text_mining_result:
                text_mining_result.count = count
            else:
                text_mining_result = TextMiningResult(
                    term=dosage_form,
                    term_type='dosage_form',
                    count=count
                )
                self.db.add(text_mining_result)
        
        # Commit changes
        self.db.commit()
        
        logger.info("Saved text mining results")
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[str]: List of extracted terms
        """
        # Normalize text
        text = text.lower()
        
        # Remove special characters and split into words
        words = re.findall(r'\b[a-z]+\b', text)
        
        # Filter out short words and common stop words
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'for', 'with', 'to'}
        terms = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return terms
    
    def _extract_ingredients(self, text: str) -> List[str]:
        """Extract potential active ingredients from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[str]: List of potential ingredients
        """
        text = text.lower()
        found_ingredients = []
        
        # Check for common ingredients
        for ingredient in self.COMMON_INGREDIENTS:
            if ingredient in text:
                found_ingredients.append(ingredient)
        
        # Look for chemical-sounding suffixes
        chemical_suffixes = ['ate', 'ide', 'ine', 'ol', 'one', 'ic', 'il', 'in']
        words = re.findall(r'\b[a-z]+\b', text)
        
        for word in words:
            if len(word) > 5 and any(word.endswith(suffix) for suffix in chemical_suffixes):
                if word not in found_ingredients:
                    found_ingredients.append(word)
        
        return found_ingredients
    
    def _extract_dosage_forms(self, text: str) -> List[str]:
        """Extract potential dosage forms from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[str]: List of potential dosage forms
        """
        text = text.lower()
        found_forms = []
        
        # Check for common dosage forms
        for form in self.DOSAGE_FORMS:
            if form in text:
                found_forms.append(form)
        
        return found_forms
