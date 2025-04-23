import logging
from scrapers import DrugClassesScraper


# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run the scraper."""
    logger.info("Starting Drug Classes Scraper")
    
    scraper = DrugClassesScraper(headless=True)
    drug_classes = list(scraper.scrape_all_drug_classes())
    
    if drug_classes:

        # Print summary
        print(f"\nScraping Summary:")
        print(f"Total drug classes scraped: {len(drug_classes)}")

        # Find and print the drug class with the longest name
        if drug_classes:
            longest_name_drug_class = max(drug_classes, key=lambda dc: len(dc.name))
            print(f"\nDrug class with the longest name:")
            print(f"Name: {longest_name_drug_class.name}")
            print(f"Length: {len(longest_name_drug_class.name)} characters")
            print(f"URL: {longest_name_drug_class.url}")

    else:
        logger.error("No drug classes were scraped")


if __name__ == "__main__":
    main()
