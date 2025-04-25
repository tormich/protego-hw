import argparse
import logging
from typing import List, Optional, Generator, Type, Any, Union

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import BinaryExpression

from models.dailymed import DrugClass
from scraper.scrapers import DrugClassesScraper, DrugScraper
from settings import get_db

logger = logging.getLogger(__name__)


def insert_batch(db, drug_classes: List[DrugClass]) -> int:
    """Insert or update a batch of drug classes into the database using UPSERT.
is_analyzed
    Args:
        db: Database session from get_db()
        drug_classes: List of drug classes to insert or update

    Returns:
        int: Number of successfully inserted/updated records
    """
    if not drug_classes:
        return 0

    # Keep track of successfully processed records
    processed_count = 0
    inserted_count = 0
    updated_count = 0

    try:
        # Prepare data for bulk upsert
        data = [
            {"name": drug.name, "url": drug.url}
            for drug in drug_classes
        ]

        # Use SQLAlchemy Core for the UPSERT operation
        from sqlalchemy.dialects.postgresql import insert
        from sqlalchemy import update

        # Define the table
        table = DrugClass.__table__

        # Perform the UPSERT operation for each record
        for item in data:
            # Create an insert statement
            stmt = insert(table).values(name=item["name"], url=item["url"])

            # Add the ON CONFLICT DO UPDATE clause
            stmt = stmt.on_conflict_do_update(
                index_elements=['name', 'url'],  # The unique constraint
                set_={"updated_at": func.now()}  # Update the updated_at timestamp
            )

            # Execute the statement
            result = db.execute(stmt)

            # Check if a new row was inserted or an existing row was updated
            if result.rowcount > 0:
                if hasattr(result, 'inserted_primary_key') and result.inserted_primary_key:
                    inserted_count += 1
                else:
                    updated_count += 1

            processed_count += 1

        # Commit the transaction
        db.commit()

        logger.info(
            f"Processed batch of {processed_count} drug classes (inserted: {inserted_count}, updated: {updated_count})")
    except Exception as e:
        # If any error occurs, rollback and log the error
        db.rollback()
        logger.error(f"Error during batch upsert: {e}")

    return processed_count


def get_all_by_batches(model: Type[Any], batch_size: int = 50,
                    where_clause: Optional[Union[BinaryExpression, List[BinaryExpression]]] = None,
                    order_by: Optional[Any] = None) -> Generator[Any, None, None]:
    """
    Generic function to query records from any model in batches and yield them one by one.

    Args:
        model: The SQLAlchemy model class to query
        batch_size: Number of records to fetch in each batch
        where_clause: Optional filter condition(s) for the query
        order_by: Optional ordering for the query (defaults to model.id)

    Yields:
        Records from the database, one at a time
    """
    with get_db() as db:
        # Build the base query
        query = db.query(model)

        # Add where clause if provided
        if where_clause is not None:
            if isinstance(where_clause, list):
                for condition in where_clause:
                    query = query.filter(condition)
            else:
                query = query.filter(where_clause)

        # Get total count for logging
        total_count = query.count()
        logger.info(f"Found {total_count} {model.__name__} records in the database")

        # Add ordering
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # Default ordering by id
            query = query.order_by(model.id)

        # Query in batches
        offset = 0
        processed_count = 0

        while True:
            # Get a batch of records
            batch = query.limit(batch_size).offset(offset).all()

            # If no more records, break the loop
            if not batch:
                break

            # Yield each record in the batch
            for record in batch:
                yield record
                processed_count += 1

                # Log progress at regular intervals
                if processed_count % (batch_size * 10) == 0 or processed_count == total_count:
                    logger.info(f"Processed {processed_count}/{total_count} {model.__name__} records")

            # Update offset for the next batch
            offset += batch_size

        logger.info(f"Completed processing {processed_count} {model.__name__} records")


def get_dailymed_drugs(batch_size: int = 50):
    """Get unanalyzed drug classes from the database in batches to optimize memory usage.

    Args:
        batch_size: Number of drug classes to query in each batch
    """
    drug_scraper = DrugScraper()

    # Get database session using context manager
    with get_db() as db:
        # Check how many unanalyzed drug classes we have
        unanalyzed_count = db.query(func.count(DrugClass.id)).filter(DrugClass.analyzed == False).scalar()
        logger.info(f"Found {unanalyzed_count} unanalyzed drug classes in the database")

        if unanalyzed_count == 0:
            logger.info("No unanalyzed drug classes found. Nothing to process.")
            return

        # Process only unanalyzed drug classes
        total_processed = 0

        # Use get_all_by_batches to process unanalyzed drug classes
        for drugclass in get_all_by_batches(
            DrugClass,
            batch_size=batch_size,
            where_clause=DrugClass.analyzed == False
        ):
            # Process the drug class
            drug_scraper.extract_drugs(drugclass.url)

            # Mark as analyzed
            drugclass.analyzed = True

            # Increment counter
            total_processed += 1

            # Commit every batch_size records
            if total_processed % batch_size == 0:
                db.commit()
                logger.info(f"Processed {total_processed}/{unanalyzed_count} unanalyzed drug classes")

        # Final commit for any remaining changes
        if total_processed % batch_size != 0:
            db.commit()

        logger.info(f"Completed processing {total_processed} unanalyzed drug classes")


def get_dailymed_drugclasses(batch_size: int = 50):
    """function to get drug classes from dailymed and save them in the database.

    Args:
        batch_size: Number of drug classes to insert in each batch
    """
    logger.info(f"Starting Drug Classes Scraper with batch size: {batch_size}")

    scraper = DrugClassesScraper()
    batch = []
    total_processed = 0

    # Get database session using context manager
    with get_db() as db:
        # First, let's check if we already have data in the database
        existing_count = db.query(func.count(DrugClass.id)).scalar()
        logger.info(f"Found {existing_count} existing drug classes in the database")

        for drug in scraper.scrape_all_drug_classes():
            new_drug = DrugClass(name=drug.name, url=drug.url)
            batch.append(new_drug)

            # When batch reaches the specified size, process it
            if len(batch) >= batch_size:
                processed = insert_batch(db, batch)
                total_processed += processed
                batch = []  # Reset the batch
                logger.info(f"Processed {total_processed} drug classes so far")

        # Process any remaining items in the batch
        if batch:
            processed = insert_batch(db, batch)
            total_processed += processed

        # Get the final count
        final_count = db.query(func.count(DrugClass.id)).scalar()
        new_count = final_count - existing_count
        logger.info(f"Total drug classes in database: {final_count}")
        logger.info(f"Processed {total_processed} drug classes")
        logger.info(f"Added {new_count} new records to the database")


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Scrape drug classes from DailyMed")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of drug classes to insert in each database batch (default: 50)"
    )

    args = parser.parse_args()
    get_dailymed_drugclasses(batch_size=args.batch_size)
