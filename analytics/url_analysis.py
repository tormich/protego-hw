"""
URL pattern analysis module.

This module provides functionality for analyzing URL patterns in drug data.
"""

import logging
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter
from urllib.parse import urlparse

from sqlalchemy import func, distinct, and_, or_

from models.dailymed import Drug, DrugClass
from models.analytics import URLAnalysis, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class URLAnalyzer(BaseAnalyzer):
    """Analyzer for URL patterns."""

    def analyze(self) -> Dict[str, Any]:
        """Analyze URL patterns.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting URL pattern analysis")
        
        # Initialize results dictionary
        results = {
            "url_structure": {},
            "path_depth": {
                "distribution": {},
                "avg_depth": 0,
            },
            "domain_distribution": {},
            "summary": {
                "total_urls": 0,
                "unique_domains": 0,
                "unique_patterns": 0,
            }
        }
        
        # Get all drug URLs
        drug_urls = self.db.query(Drug.url).all()
        drug_urls = [url[0] for url in drug_urls if url[0]]
        
        # Get all drug class URLs
        class_urls = self.db.query(DrugClass.url).all()
        class_urls = [url[0] for url in class_urls if url[0]]
        
        # Combine all URLs
        all_urls = drug_urls + class_urls
        results["summary"]["total_urls"] = len(all_urls)
        
        # Process URLs
        url_patterns = []
        path_depths = []
        domains = []
        
        for url in all_urls:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Extract domain
            domain = parsed_url.netloc
            domains.append(domain)
            
            # Extract path and calculate depth
            path = parsed_url.path
            path_parts = [p for p in path.split('/') if p]
            path_depth = len(path_parts)
            path_depths.append(path_depth)
            
            # Extract pattern (replace specific IDs with placeholders)
            pattern = self._extract_url_pattern(path)
            url_patterns.append(pattern)
        
        # Calculate URL pattern frequencies
        pattern_counter = Counter(url_patterns)
        results["url_structure"] = dict(pattern_counter.most_common(20))
        
        # Calculate path depth distribution
        depth_counter = Counter(path_depths)
        results["path_depth"]["distribution"] = dict(sorted(depth_counter.items()))
        
        if path_depths:
            results["path_depth"]["avg_depth"] = sum(path_depths) / len(path_depths)
        
        # Calculate domain distribution
        domain_counter = Counter(domains)
        results["domain_distribution"] = dict(domain_counter.most_common(10))
        results["summary"]["unique_domains"] = len(domain_counter)
        
        # Count unique patterns
        results["summary"]["unique_patterns"] = len(pattern_counter)
        
        logger.info(f"Completed URL pattern analysis. Processed {len(all_urls)} URLs.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving URL pattern analysis results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="URLAnalyzer",
            result_type="url_analysis",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save URL pattern analysis
        for pattern, count in results["url_structure"].items():
            # Calculate average depth for this pattern
            pattern_depth = len([p for p in pattern.split('/') if p])
            
            url_analysis = self.db.query(URLAnalysis).filter(URLAnalysis.pattern == pattern).first()
            
            if url_analysis:
                url_analysis.count = count
                url_analysis.avg_depth = pattern_depth
            else:
                # Extract domain from the first URL with this pattern
                domain = None
                for url in self.db.query(Drug.url).all():
                    if url[0] and self._extract_url_pattern(urlparse(url[0]).path) == pattern:
                        domain = urlparse(url[0]).netloc
                        break
                
                url_analysis = URLAnalysis(
                    pattern=pattern,
                    count=count,
                    avg_depth=pattern_depth,
                    domain=domain
                )
                self.db.add(url_analysis)
        
        # Commit changes
        self.db.commit()
        
        logger.info(f"Saved URL pattern analysis results for {len(results['url_structure'])} patterns")
    
    def _extract_url_pattern(self, path: str) -> str:
        """Extract a pattern from a URL path by replacing numeric IDs with placeholders.
        
        Args:
            path: URL path to analyze
            
        Returns:
            str: URL pattern with IDs replaced by placeholders
        """
        # Replace numeric IDs with {id}
        pattern = re.sub(r'/\d+/', '/{id}/', path)
        
        # Replace UUIDs with {uuid}
        pattern = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/', '/{uuid}/', pattern)
        
        return pattern
