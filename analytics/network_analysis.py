"""
Network analysis module.

This module provides functionality for analyzing network relationships in drug data.
"""

import logging
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict

from sqlalchemy import func, distinct, and_, or_, insert

from models.dailymed import Drug, DrugClass
from models.analytics import DrugRelationship, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class NetworkAnalyzer(BaseAnalyzer):
    """Analyzer for network relationships."""

    def analyze(self) -> Dict[str, Any]:
        """Analyze network relationships.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting network analysis")

        # Initialize results dictionary
        results = {
            "drug_similarity": {
                "by_ndc": [],
                "by_name": [],
            },
            "class_relationships": [],
            "co_occurrence": [],
            "summary": {
                "total_relationships": 0,
                "total_drugs": 0,
                "total_classes": 0,
            }
        }

        # Get all drugs
        drugs = self.db.query(Drug).all()
        results["summary"]["total_drugs"] = len(drugs)

        # Get all drug classes
        drug_classes = self.db.query(DrugClass).all()
        results["summary"]["total_classes"] = len(drug_classes)

        # Analyze drug similarity based on NDC codes
        ndc_relationships = self._analyze_ndc_similarity(drugs)
        results["drug_similarity"]["by_ndc"] = ndc_relationships

        # Analyze drug similarity based on name
        name_relationships = self._analyze_name_similarity(drugs)
        results["drug_similarity"]["by_name"] = name_relationships

        # Analyze drug class relationships
        class_relationships = self._analyze_class_relationships(drug_classes)
        results["class_relationships"] = class_relationships

        # Analyze drug co-occurrence (drugs in the same class)
        co_occurrence = self._analyze_co_occurrence(drugs)
        results["co_occurrence"] = co_occurrence

        # Count total relationships
        total_relationships = (
            len(ndc_relationships) +
            len(name_relationships) +
            len(class_relationships) +
            len(co_occurrence)
        )
        results["summary"]["total_relationships"] = total_relationships

        logger.info(f"Completed network analysis. Found {total_relationships} relationships.")

        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving network analysis results")

        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="NetworkAnalyzer",
            result_type="network_analysis",
            result_data=results
        )
        self.db.add(analytics_result)

        # Save drug relationships
        relationships_to_save = []

        # Add NDC-based relationships
        for rel in results["drug_similarity"]["by_ndc"]:
            relationships_to_save.append({
                "source_drug_id": rel["source_id"],
                "target_drug_id": rel["target_id"],
                "relationship_type": "ndc_similarity",
                "weight": rel["weight"]
            })

        # Add name-based relationships
        for rel in results["drug_similarity"]["by_name"]:
            relationships_to_save.append({
                "source_drug_id": rel["source_id"],
                "target_drug_id": rel["target_id"],
                "relationship_type": "name_similarity",
                "weight": rel["weight"]
            })

        # Add co-occurrence relationships
        for rel in results["co_occurrence"]:
            relationships_to_save.append({
                "source_drug_id": rel["source_id"],
                "target_drug_id": rel["target_id"],
                "relationship_type": "co_occurrence",
                "weight": rel["weight"]
            })

        # Save relationships in batches
        batch_size = 100
        for i in range(0, len(relationships_to_save), batch_size):
            batch = relationships_to_save[i:i+batch_size]

            # Handle conflicts manually by checking if relationships already exist
            for rel in batch:
                # Check if relationship already exists
                existing = self.db.query(DrugRelationship).filter_by(
                    source_drug_id=rel['source_drug_id'],
                    target_drug_id=rel['target_drug_id']
                ).first()

                if not existing:
                    # Create new relationship
                    new_relationship = DrugRelationship(
                        source_drug_id=rel['source_drug_id'],
                        target_drug_id=rel['target_drug_id'],
                        relationship_type=rel['relationship_type'],
                        weight=rel['weight']
                    )
                    self.db.add(new_relationship)

        # Commit changes
        self.db.commit()

        logger.info(f"Saved {len(relationships_to_save)} drug relationships")

    def _analyze_ndc_similarity(self, drugs: List[Drug]) -> List[Dict[str, Any]]:
        """Analyze drug similarity based on shared NDC codes.

        Args:
            drugs: List of Drug objects

        Returns:
            List[Dict[str, Any]]: List of drug relationships
        """
        relationships = []

        # Create a mapping of NDC codes to drugs
        ndc_to_drugs = defaultdict(list)

        for drug in drugs:
            if not drug.ndc_codes:
                continue

            for ndc in drug.ndc_codes:
                ndc_to_drugs[ndc].append(drug.id)

        # Find drugs that share NDC codes
        for ndc, drug_ids in ndc_to_drugs.items():
            if len(drug_ids) < 2:
                continue

            # Create relationships between all pairs of drugs sharing this NDC
            for i, source_id in enumerate(drug_ids):
                for target_id in drug_ids[i+1:]:
                    # Check if this relationship already exists
                    existing = False
                    for rel in relationships:
                        if (rel["source_id"] == source_id and rel["target_id"] == target_id) or \
                           (rel["source_id"] == target_id and rel["target_id"] == source_id):
                            # Increase weight for existing relationship
                            rel["weight"] += 1
                            existing = True
                            break

                    if not existing:
                        # Create new relationship
                        relationships.append({
                            "source_id": source_id,
                            "target_id": target_id,
                            "type": "ndc_similarity",
                            "shared_ndc": ndc,
                            "weight": 1
                        })

        return relationships

    def _analyze_name_similarity(self, drugs: List[Drug]) -> List[Dict[str, Any]]:
        """Analyze drug similarity based on name similarity.

        Args:
            drugs: List of Drug objects

        Returns:
            List[Dict[str, Any]]: List of drug relationships
        """
        relationships = []

        # Group drugs by the first 3 letters of their name
        name_prefix_to_drugs = defaultdict(list)

        for drug in drugs:
            if not drug.name or len(drug.name) < 3:
                continue

            prefix = drug.name[:3].lower()
            name_prefix_to_drugs[prefix].append(drug)

        # Find drugs with similar names
        for prefix, similar_drugs in name_prefix_to_drugs.items():
            if len(similar_drugs) < 2:
                continue

            # Create relationships between all pairs of drugs with similar names
            for i, source_drug in enumerate(similar_drugs):
                for target_drug in similar_drugs[i+1:]:
                    # Calculate similarity score (simple implementation)
                    similarity = self._calculate_name_similarity(source_drug.name, target_drug.name)

                    # Only include relationships with significant similarity
                    if similarity > 0.7:
                        relationships.append({
                            "source_id": source_drug.id,
                            "target_id": target_drug.id,
                            "type": "name_similarity",
                            "similarity": similarity,
                            "weight": similarity
                        })

        return relationships

    def _analyze_class_relationships(self, drug_classes: List[DrugClass]) -> List[Dict[str, Any]]:
        """Analyze relationships between drug classes.

        Args:
            drug_classes: List of DrugClass objects

        Returns:
            List[Dict[str, Any]]: List of drug class relationships
        """
        relationships = []

        # Create a mapping of class name parts to classes
        name_part_to_classes = defaultdict(list)

        for drug_class in drug_classes:
            # Split class name by common separators
            parts = drug_class.name.split('/')

            for part in parts:
                part = part.strip().lower()
                if part:
                    name_part_to_classes[part].append(drug_class)

        # Find classes that share name parts
        for part, classes in name_part_to_classes.items():
            if len(classes) < 2:
                continue

            # Create relationships between all pairs of classes sharing this name part
            for i, source_class in enumerate(classes):
                for target_class in classes[i+1:]:
                    relationships.append({
                        "source_id": source_class.id,
                        "target_id": target_class.id,
                        "type": "shared_name_part",
                        "shared_part": part,
                        "weight": 1
                    })

        return relationships

    def _analyze_co_occurrence(self, drugs: List[Drug]) -> List[Dict[str, Any]]:
        """Analyze drug co-occurrence (drugs in the same class).

        Args:
            drugs: List of Drug objects

        Returns:
            List[Dict[str, Any]]: List of drug co-occurrence relationships
        """
        relationships = []

        # Group drugs by drug class
        class_to_drugs = defaultdict(list)

        for drug in drugs:
            if drug.drug_class_id:
                class_to_drugs[drug.drug_class_id].append(drug)

        # Find drugs that co-occur in the same class
        for class_id, class_drugs in class_to_drugs.items():
            if len(class_drugs) < 2:
                continue

            # Create relationships between all pairs of drugs in the same class
            for i, source_drug in enumerate(class_drugs):
                for target_drug in class_drugs[i+1:]:
                    relationships.append({
                        "source_id": source_drug.id,
                        "target_id": target_drug.id,
                        "type": "co_occurrence",
                        "class_id": class_id,
                        "weight": 1
                    })

        return relationships

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two drug names.

        Args:
            name1: First drug name
            name2: Second drug name

        Returns:
            float: Similarity score between 0 and 1
        """
        # Simple implementation using Jaccard similarity of character trigrams
        def get_trigrams(text):
            text = text.lower()
            return set(text[i:i+3] for i in range(len(text)-2))

        trigrams1 = get_trigrams(name1)
        trigrams2 = get_trigrams(name2)

        if not trigrams1 or not trigrams2:
            return 0

        # Calculate Jaccard similarity
        intersection = len(trigrams1.intersection(trigrams2))
        union = len(trigrams1.union(trigrams2))

        return intersection / union if union > 0 else 0
