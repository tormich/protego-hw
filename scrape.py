import logging
import argparse
from typing import List

from scraper.scrapers import DrugClassesScraper
from models.dailymed import DrugClass

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from sqlalchemy import func, exists
from sqlalchemy.exc import IntegrityError
from settings import engine


def insert_batch(session: Session, drug_classes: List[DrugClass]) -> int:
    """Insert or update a batch of drug classes into the database using UPSERT.

    Args:
        session: SQLAlchemy session
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
            result = session.execute(stmt)

            # Check if a new row was inserted or an existing row was updated
            if result.rowcount > 0:
                if hasattr(result, 'inserted_primary_key') and result.inserted_primary_key:
                    inserted_count += 1
                else:
                    updated_count += 1

            processed_count += 1

        # Commit the transaction
        session.commit()

        logger.info(f"Processed batch of {processed_count} drug classes (inserted: {inserted_count}, updated: {updated_count})")
    except Exception as e:
        # If any error occurs, rollback and log the error
        session.rollback()
        logger.error(f"Error during batch upsert: {e}")

    return processed_count


def main(batch_size: int = 50):
    """Main function to run the scraper.

    Args:
        batch_size: Number of drug classes to insert in each batch
    """
    logger.info(f"Starting Drug Classes Scraper with batch size: {batch_size}")

    scraper = DrugClassesScraper()
    batch = []
    total_processed = 0

    with Session(engine) as session:
        # First, let's check if we already have data in the database
        existing_count = session.query(func.count(DrugClass.id)).scalar()
        logger.info(f"Found {existing_count} existing drug classes in the database")

        for drug in scraper.scrape_all_drug_classes():
            new_drug = DrugClass(name=drug.name, url=drug.url)
            batch.append(new_drug)

            # When batch reaches the specified size, process it
            if len(batch) >= batch_size:
                processed = insert_batch(session, batch)
                total_processed += processed
                batch = []  # Reset the batch
                logger.info(f"Processed {total_processed} drug classes so far")

        # Process any remaining items in the batch
        if batch:
            processed = insert_batch(session, batch)
            total_processed += processed

        # Get the final count
        final_count = session.query(func.count(DrugClass.id)).scalar()
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
    main(batch_size=args.batch_size)
