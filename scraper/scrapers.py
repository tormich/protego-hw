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


class Drug(BaseModel):
    name: str = Field(..., description="The name of the drug")
    url: str = Field(..., description="The URL to the drug page")
    ndc_codes: List[str] = Field(default_factory=list, description="List of NDC codes for the drug")
    active_ingredients: List[str] = Field(default_factory=list, description="List of active ingredients in the drug")
    dosage_form: Optional[str] = Field(None, description="The dosage form of the drug")
    route: Optional[str] = Field(None, description="The route of administration")


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


class DrugScraper(RequestsScraper):
    """Scraper for drugs from DailyMed website."""

    # CSS selectors for drug listings and details
    drug_listing_selector = "article.row"
    drug_name_selector = ".drug-name a.drug-info-link"
    ndc_code_selector = ".ndc-codes"
    active_ingredient_selector = ".active-ingredients"
    dosage_form_selector = ".dosage-form"
    route_selector = ".route"

    # Selectors for drug detail page
    ndc_codes_detail_selector = "#ndc-codes-section table tbody tr"
    active_ingredients_detail_selector = "#active-ingredients-section .active-ingredient"

    def extract_drugs(self, url: str) -> List[Drug]:
        """
        Extract drugs from the specified URL.

        Args:
            url: The URL to the page containing drug listings

        Returns:
            List[Drug]: List of drugs found on the page
        """
        drugs = []
        soup = self.get_url(url)

        if not soup:
            logger.error(f"Failed to load drug listing page: {url}")
            return drugs

        try:
            # Find all drug rows in the table
            drug_rows = soup.select(self.drug_listing_selector)
            logger.info(f"Found {len(drug_rows)} drug entries on page {url}")

            for row in drug_rows:
                try:
                    # Extract drug name and URL
                    name_element = row.select_one(self.drug_name_selector)
                    if not name_element:
                        continue

                    name = name_element.text.strip()
                    relative_url = name_element.get('href')
                    absolute_url = urljoin(BASE_URL, relative_url) if relative_url else None

                    if not name or not absolute_url:
                        continue

                    # Extract basic information from the listing
                    ndc_code_element = row.select_one(self.ndc_code_selector)
                    ndc_codes = []
                    if ndc_code_element:
                        # Clean up and split NDC codes
                        ndc_text = ndc_code_element.text.strip()
                        # Remove 'view more' text
                        ndc_text = ndc_text.replace('view more', '')
                        # Split by commas and clean up each code
                        for code in ndc_text.split(','):
                            code = code.strip()
                            if code:
                                ndc_codes.append(code)

                    active_ingredient_element = row.select_one(self.active_ingredient_selector)
                    active_ingredients = []
                    if active_ingredient_element:
                        # Clean up and split active ingredients
                        ingredient_text = active_ingredient_element.text.strip()
                        # Split by commas and clean up each ingredient
                        for ingredient in ingredient_text.split(','):
                            ingredient = ingredient.strip()
                            if ingredient:
                                active_ingredients.append(ingredient)

                    dosage_form_element = row.select_one(self.dosage_form_selector)
                    dosage_form = dosage_form_element.text.strip() if dosage_form_element else None

                    route_element = row.select_one(self.route_selector)
                    route = route_element.text.strip() if route_element else None

                    # Create drug object with basic information
                    drug = Drug(
                        name=name,
                        url=absolute_url,
                        ndc_codes=ndc_codes,
                        active_ingredients=active_ingredients,
                        dosage_form=dosage_form,
                        route=route
                    )

                    # Optionally fetch detailed information
                    # self._enrich_drug_details(drug)

                    drugs.append(drug)
                    logger.info(f"Extracted drug: {name}")

                except Exception as e:
                    logger.error(f"Error extracting drug from row: {e}")
                    continue

            logger.info(f"Extracted {len(drugs)} drugs from {url}")
            return drugs

        except Exception as e:
            logger.error(f"Error extracting drugs from {url}: {e}")
            return drugs

    def _enrich_drug_details(self, drug: Drug) -> None:
        """
        Fetch additional details for a drug from its detail page.

        Args:
            drug: The drug object to enrich with additional details
        """
        soup = self.get_url(drug.url)
        if not soup:
            logger.warning(f"Could not fetch details for drug: {drug.name}")
            return

        try:
            # Extract NDC codes from detail page
            ndc_rows = soup.select(self.ndc_codes_detail_selector)
            ndc_codes = []
            for row in ndc_rows:
                code_cell = row.select_one("td:nth-child(1)")
                if code_cell and code_cell.text.strip():
                    ndc_codes.append(code_cell.text.strip())

            if ndc_codes:
                drug.ndc_codes = ndc_codes

            # Extract active ingredients from detail page
            ingredient_elements = soup.select(self.active_ingredients_detail_selector)
            active_ingredients = []
            for element in ingredient_elements:
                if element.text.strip():
                    active_ingredients.append(element.text.strip())

            if active_ingredients:
                drug.active_ingredients = active_ingredients

            logger.info(f"Enriched drug details for {drug.name}: {len(drug.ndc_codes)} NDC codes, {len(drug.active_ingredients)} ingredients")

        except Exception as e:
            logger.error(f"Error enriching drug details for {drug.name}: {e}")
