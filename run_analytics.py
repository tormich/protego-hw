"""
Main script to run analytics on drug data.
"""

import argparse
import logging
import time
from typing import List, Optional

import settings
from analytics import (
    NDCAnalyzer,
    ClassificationAnalyzer,
    NameAnalyzer,
    URLAnalyzer,
    TimeAnalyzer,
    NetworkAnalyzer,
    TextMiningAnalyzer,
)

logger = logging.getLogger(__name__)


def run_analytics(analyzers: Optional[List[str]] = None):
    """Run the specified analytics.

    Args:
        analyzers: List of analyzer names to run. If None, run all analyzers.
    """
    # Map of analyzer names to analyzer classes
    analyzer_map = {
        'ndc': NDCAnalyzer,
        'classification': ClassificationAnalyzer,
        'name': NameAnalyzer,
        'url': URLAnalyzer,
        'time': TimeAnalyzer,
        'network': NetworkAnalyzer,
        'text': TextMiningAnalyzer,
    }
    
    # If no analyzers specified, run all
    if not analyzers:
        analyzers = list(analyzer_map.keys())
    
    # Run each specified analyzer
    for analyzer_name in analyzers:
        if analyzer_name not in analyzer_map:
            logger.warning(f"Unknown analyzer: {analyzer_name}")
            continue
        
        logger.info(f"Running {analyzer_name} analyzer")
        start_time = time.time()
        
        # Create and run the analyzer
        analyzer_class = analyzer_map[analyzer_name]
        analyzer = analyzer_class()
        results = analyzer.run()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed {analyzer_name} analyzer in {elapsed_time:.2f} seconds")
        
        # Log a summary of the results
        if 'summary' in results:
            logger.info(f"Summary: {results['summary']}")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run analytics on drug data")
    parser.add_argument(
        "--analyzers",
        nargs="+",
        choices=['ndc', 'classification', 'name', 'url', 'time', 'network', 'text', 'all'],
        help="Analyzers to run (default: all)"
    )
    
    args = parser.parse_args()
    
    # Handle 'all' option
    if args.analyzers and 'all' in args.analyzers:
        args.analyzers = None
    
    # Run the analytics
    run_analytics(args.analyzers)
