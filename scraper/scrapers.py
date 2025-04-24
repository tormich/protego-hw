import logging
import time
from typing import List, Optional, Generator
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException, Timeout
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

BASE_URL = "https://dailymed.nlm.nih.gov"
FIRST_PAGE_URL = f"{BASE_URL}/dailymed/browse-drug-classes.cfm"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
PAGE_LOAD_TIMEOUT = 10  # seconds


class DrugClass(BaseModel):
    name: str = Field(..., description="The name of the drug class")
    url: str = Field(..., description="The URL to the drug class page")


class RequestsScraper:
    """Base class for scrapers using requests"""

    def __init__(self):
        """
        Initialize the scraper.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        })

    def get_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get the specified URL with retry logic and return a BeautifulSoup object.

        Args:
            url: The URL to get

        Returns:
            Optional[BeautifulSoup]: BeautifulSoup object if successful, None otherwise
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Getting {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                response = self.session.get(url, timeout=PAGE_LOAD_TIMEOUT)
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses

                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup

            except Timeout:
                logger.warning(f"Timeout while loading {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Failed to load {url} after {MAX_RETRIES} attempts")
                    return None
            except RequestException as e:
                logger.error(f"Request error while loading {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
            except Exception as e:
                logger.error(f"Unexpected error while loading {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
        return None


class DrugClassesScraper(RequestsScraper):
    """Scraper for drug classes from DailyMed website."""

    listing_css_selector = "#listing > ul > li > a"
    drug_class_css_selector = "#double > li > a"

    def extract_drug_classes_from_page(self, soup: BeautifulSoup) -> List[DrugClass]:
        """
        Extract drug classes from the BeautifulSoup object.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List[DrugClass]: List of drug classes found on the page
        """
        drug_classes = []
        try:
            # Find all drug class links in the table
            drug_class_elements = soup.select(self.drug_class_css_selector)

            for element in drug_class_elements:
                name = element.text.strip()
                relative_url = element.get('href')
                absolute_url = urljoin(BASE_URL, relative_url)

                logger.info(f"Found {name} leading to {absolute_url}")

                if name and absolute_url:
                    drug_classes.append(DrugClass(name=name, url=absolute_url))

            logger.info(f"Extracted {len(drug_classes)} drug classes from current page")
            return drug_classes

        except Exception as e:
            logger.error(f"Error extracting drug classes: {e}")
            return []

    def collect_all_page_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Collect all page links from the pagination section.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List[str]: List of URLs for all pages
        """
        try:
            # Find all page links
            page_links = soup.select(self.listing_css_selector)

            # Extract URLs from the links
            page_urls = []
            for link in page_links:
                url = link.get('href')
                if url:
                    page_urls.append(url)

            logger.info(f"Collected {len(page_urls)} page links")
            return page_urls

        except Exception as e:
            logger.error(f"Error collecting page links: {e}")
            return []

    def scrape_all_drug_classes(self) -> Generator[DrugClass, None, None]:
        """
        Scrape all drug classes from all pages.

        Returns:
            Generator[DrugClass, None, None]: Generator yielding drug classes
        """
        try:
            # Get the initial page
            initial_soup = self.get_url(FIRST_PAGE_URL)
            if not initial_soup:
                logger.error("Failed to navigate to the initial URL")
                return

            # Collect all page links first
            page_urls = self.collect_all_page_links(initial_soup)
            if not page_urls:
                logger.error("No page links found")
                return

            # Process the first page
            for drug_class in self.extract_drug_classes_from_page(initial_soup):
                yield drug_class

            # Process remaining pages
            for page_url in page_urls[1:]:  # Skip the first page as we've already processed it
                page_soup = self.get_url(f"{BASE_URL}{page_url}")
                if not page_soup:
                    logger.error(f"Failed to navigate to page: {page_url}")
                    continue

                for drug_class in self.extract_drug_classes_from_page(page_soup):
                    yield drug_class

        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            return

