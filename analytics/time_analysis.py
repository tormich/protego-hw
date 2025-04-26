"""
Time-based analysis module.

This module provides functionality for analyzing time-based patterns in drug data.
"""

import logging
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, distinct, and_, or_, extract

from models.dailymed import Drug, DrugClass
from models.analytics import TimeAnalysis, AnalyticsResult
from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class TimeAnalyzer(BaseAnalyzer):
    """Analyzer for time-based patterns."""

    def analyze(self) -> Dict[str, Any]:
        """Analyze time-based patterns.

        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info("Starting time-based analysis")
        
        # Initialize results dictionary
        results = {
            "creation_trends": {
                "daily": {},
                "weekly": {},
                "monthly": {},
                "yearly": {},
            },
            "update_frequency": {
                "avg_days_between_updates": 0,
                "distribution": {},
            },
            "seasonal_patterns": {
                "by_month": {},
                "by_day_of_week": {},
            },
            "summary": {
                "oldest_record": None,
                "newest_record": None,
                "total_records": 0,
            }
        }
        
        # Get creation dates for drugs
        drug_dates = self.db.query(Drug.created_at, Drug.updated_at).all()
        
        # Get creation dates for drug classes
        class_dates = self.db.query(DrugClass.created_at, DrugClass.updated_at).all()
        
        # Combine all dates
        all_created_dates = [d[0] for d in drug_dates + class_dates if d[0]]
        all_updated_dates = [d[1] for d in drug_dates + class_dates if d[1]]
        
        results["summary"]["total_records"] = len(all_created_dates)
        
        if all_created_dates:
            # Find oldest and newest records
            oldest_date = min(all_created_dates)
            newest_date = max(all_created_dates)
            
            results["summary"]["oldest_record"] = oldest_date.isoformat()
            results["summary"]["newest_record"] = newest_date.isoformat()
            
            # Analyze creation trends
            self._analyze_time_trends(all_created_dates, results["creation_trends"])
            
            # Analyze seasonal patterns
            self._analyze_seasonal_patterns(all_created_dates, results["seasonal_patterns"])
        
        # Analyze update frequency
        if all_updated_dates:
            update_intervals = []
            
            # For each record with both creation and update dates, calculate the interval
            for created, updated in zip(all_created_dates, all_updated_dates):
                if created and updated and updated > created:
                    interval_days = (updated - created).days
                    update_intervals.append(interval_days)
            
            if update_intervals:
                results["update_frequency"]["avg_days_between_updates"] = sum(update_intervals) / len(update_intervals)
                
                # Create distribution of update intervals
                interval_distribution = defaultdict(int)
                for interval in update_intervals:
                    # Group intervals into buckets
                    if interval < 1:
                        bucket = "same_day"
                    elif interval < 7:
                        bucket = "within_week"
                    elif interval < 30:
                        bucket = "within_month"
                    elif interval < 90:
                        bucket = "within_quarter"
                    elif interval < 365:
                        bucket = "within_year"
                    else:
                        bucket = "over_year"
                    
                    interval_distribution[bucket] += 1
                
                results["update_frequency"]["distribution"] = dict(interval_distribution)
        
        logger.info(f"Completed time-based analysis. Processed {len(all_created_dates)} records.")
        
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to the database.

        Args:
            results: Analysis results to save
        """
        logger.info("Saving time-based analysis results")
        
        # Save overall results as JSON
        analytics_result = AnalyticsResult(
            analyzer_name="TimeAnalyzer",
            result_type="time_analysis",
            result_data=results
        )
        self.db.add(analytics_result)
        
        # Save daily trends
        for date_str, count in results["creation_trends"]["daily"].items():
            date = datetime.fromisoformat(date_str)
            
            time_analysis = self.db.query(TimeAnalysis).filter(
                and_(TimeAnalysis.time_period == 'day', TimeAnalysis.period_start == date)
            ).first()
            
            if time_analysis:
                time_analysis.count = count
            else:
                time_analysis = TimeAnalysis(
                    time_period='day',
                    period_start=date,
                    count=count
                )
                self.db.add(time_analysis)
        
        # Save monthly trends
        for month_str, count in results["creation_trends"]["monthly"].items():
            # Convert "YYYY-MM" to datetime
            year, month = map(int, month_str.split('-'))
            date = datetime(year, month, 1)
            
            time_analysis = self.db.query(TimeAnalysis).filter(
                and_(TimeAnalysis.time_period == 'month', TimeAnalysis.period_start == date)
            ).first()
            
            if time_analysis:
                time_analysis.count = count
            else:
                time_analysis = TimeAnalysis(
                    time_period='month',
                    period_start=date,
                    count=count
                )
                self.db.add(time_analysis)
        
        # Commit changes
        self.db.commit()
        
        logger.info("Saved time-based analysis results")
    
    def _analyze_time_trends(self, dates: List[datetime], trends: Dict[str, Dict[str, int]]) -> None:
        """Analyze time trends from a list of dates.
        
        Args:
            dates: List of datetime objects
            trends: Dictionary to store the trends
        """
        daily_counts = defaultdict(int)
        weekly_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        yearly_counts = defaultdict(int)
        
        for date in dates:
            # Daily trend (YYYY-MM-DD)
            daily_key = date.strftime('%Y-%m-%d')
            daily_counts[daily_key] += 1
            
            # Weekly trend (YYYY-WW)
            weekly_key = date.strftime('%Y-%W')
            weekly_counts[weekly_key] += 1
            
            # Monthly trend (YYYY-MM)
            monthly_key = date.strftime('%Y-%m')
            monthly_counts[monthly_key] += 1
            
            # Yearly trend (YYYY)
            yearly_key = date.strftime('%Y')
            yearly_counts[yearly_key] += 1
        
        # Sort and store the trends
        trends["daily"] = dict(sorted(daily_counts.items()))
        trends["weekly"] = dict(sorted(weekly_counts.items()))
        trends["monthly"] = dict(sorted(monthly_counts.items()))
        trends["yearly"] = dict(sorted(yearly_counts.items()))
    
    def _analyze_seasonal_patterns(self, dates: List[datetime], patterns: Dict[str, Dict[str, int]]) -> None:
        """Analyze seasonal patterns from a list of dates.
        
        Args:
            dates: List of datetime objects
            patterns: Dictionary to store the patterns
        """
        month_counts = defaultdict(int)
        day_of_week_counts = defaultdict(int)
        
        for date in dates:
            # Month (1-12)
            month = date.month
            month_counts[month] += 1
            
            # Day of week (0-6, where 0 is Monday)
            day_of_week = date.weekday()
            day_of_week_counts[day_of_week] += 1
        
        # Convert month numbers to names
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        month_pattern = {month_names[month]: count for month, count in sorted(month_counts.items())}
        
        # Convert day of week numbers to names
        day_names = {
            0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
            4: "Friday", 5: "Saturday", 6: "Sunday"
        }
        
        day_pattern = {day_names[day]: count for day, count in sorted(day_of_week_counts.items())}
        
        # Store the patterns
        patterns["by_month"] = month_pattern
        patterns["by_day_of_week"] = day_pattern
