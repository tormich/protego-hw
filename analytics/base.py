"""
Base analytics module for drug data analysis.

This module provides the base class for all analytics modules.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from settings import get_db

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Base class for all analytics modules."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the analyzer.

        Args:
            db_session: SQLAlchemy database session. If None, a new session will be created.
        """
        self.db = db_session

    def __enter__(self):
        """Context manager entry point."""
        if self.db is None:
            self._db_context = get_db()
            self.db = self._db_context.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if hasattr(self, '_db_context'):
            self._db_context.__exit__(exc_type, exc_val, exc_tb)
            self.db = None

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """Run the analysis.

        Returns:
            Dict[str, Any]: Analysis results
        """
        pass

    @abstractmethod
    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        pass

    def run(self) -> Dict[str, Any]:
        """Run the analysis and save the results.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info(f"Running {self.__class__.__name__}")
        
        # Use context manager to handle database session
        with self:
            # Run the analysis
            results = self.analyze()
            
            # Save the results
            self.save_results(results)
            
            logger.info(f"Completed {self.__class__.__name__}")
            
            return results
