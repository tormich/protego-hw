import logging
import time
from typing import List, Optional, Generator
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/browse-drug-classes.cfm"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
PAGE_LOAD_TIMEOUT = 10  # seconds


class DrugClass(BaseModel):
    name: str = Field(..., description="The name of the drug class")
    url: str = Field(..., description="The URL to the drug class page")


class SeleniumScraper:
    """Base class for scrapers"""

    def __init__(self, headless: bool = False, driver_path: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            headless: Whether to run the browser in headless mode
            driver_path: Path to the ChromeDriver executable
        """
        self.headless = headless
        self.driver_path = driver_path
        self.driver = None
    
    def setup_driver(self):
        """Set up the Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        # Add arguments to avoid detection as automated browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
        
        if self.driver_path:
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        logger.info("WebDriver initialized successfully")
    
    def navigate_to_url(self, url: str) -> bool:
        """
        Navigate to the specified URL with retry logic.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Navigating to {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                self.driver.get(url)
                return True
            except TimeoutException:
                logger.warning(f"Timeout while loading {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Failed to load {url} after {MAX_RETRIES} attempts")
                    return False
            except WebDriverException as e:
                logger.error(f"WebDriver error while loading {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return False
        return False
    

class DrugClassesScraper(SeleniumScraper):
    """Scraper for drug classes from DailyMed website."""
    
    listing_css_selector = "#listing > ul > li > a"
    drug_class_css_selector = "#double > li > a"
    
    def extract_drug_classes_from_page(self) -> List[DrugClass]:
        """
        Extract drug classes from the current page.
        
        Returns:
            List[DrugClass]: List of drug classes found on the page
        """
        drug_classes = []
        try:
            # Wait for the drug class table to load
            WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#double"))
            )
            
            # Find all drug class links in the table
            drug_class_elements = self.driver.find_elements(By.CSS_SELECTOR, "#double > li > a")
            
            for element in drug_class_elements:
                name = element.text.strip()
                relative_url = element.get_attribute("href")
                absolute_url = urljoin(BASE_URL, relative_url)
                
                logger.info(f"Found {name} leading to {absolute_url}")

                if name and absolute_url:
                    drug_classes.append(DrugClass(name=name, url=absolute_url))
            
            logger.info(f"Extracted {len(drug_classes)} drug classes from current page")
            return drug_classes
        
        except TimeoutException:
            logger.error("Timeout waiting for drug class table to load")
            return []
        except NoSuchElementException as e:
            logger.error(f"Element not found: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting drug classes: {e}")
            return []
    
    def collect_all_page_links(self) -> List[str]:
        """
        Collect all page links from the pagination section.
        
        Returns:
            List[str]: List of URLs for all pages
        """
        try:
            # Wait for the pagination section to load
            WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.listing_css_selector))
            )
            
            # Find all page links
            page_links = self.driver.find_elements(By.CSS_SELECTOR, self.listing_css_selector)
            
            # Extract URLs from the links
            page_urls = []
            for link in page_links:
                url = link.get_attribute("href")
                if url:
                    page_urls.append(url)
            
            logger.info(f"Collected {len(page_urls)} page links")
            return page_urls
            
        except TimeoutException:
            logger.error("Timeout waiting for pagination section to load")
            return []
        except NoSuchElementException:
            logger.error("Pagination section not found")
            return []
        except Exception as e:
            logger.error(f"Error collecting page links: {e}")
            return []

    def go_to_next_page(self, next_url: str) -> bool:
        """
        Navigate to the specified page URL.
        
        Args:
            next_url: The URL of the next page to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Navigate to the next page URL
            self.driver.get(next_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.listing_css_selector))
            )
            
            logger.info(f"Successfully navigated to page: {next_url}")
            return True
        except TimeoutException:
            logger.error(f"Timeout waiting for page to load: {next_url}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to page {next_url}: {e}")
            return False

    def scrape_all_drug_classes(self) -> Generator[DrugClass, None, None]:
        """
        Scrape all drug classes from all pages.
        
        Returns:
            Generator[DrugClass, None, None]: Generator yielding drug classes
        """
        try:
            self.setup_driver()
            
            if not self.navigate_to_url(BASE_URL):
                logger.error("Failed to navigate to the initial URL")
                return
            
            # Collect all page links first
            page_urls = self.collect_all_page_links()
            if not page_urls:
                logger.error("No page links found")
                return
            
            total_drug_classes = []
            
            # Process the first page
            for drug_class in self.extract_drug_classes_from_page():
                yield drug_class
            
            # Process remaining pages
            for page_url in page_urls[1:]:  # Skip the first page as we've already processed it
                if not self.go_to_next_page(page_url):
                    logger.error(f"Failed to navigate to page: {page_url}")
                    continue
                
                for drug_class in self.extract_drug_classes_from_page():
                    yield drug_class
            
            logger.info(f"Scraped a total of {len(total_drug_classes)} drug classes from {len(page_urls)} pages")
            
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            return
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
