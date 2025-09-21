import asyncio
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
from typing import Optional, Dict, List
from app.core.config import settings
from app.services.parser import BookMyShowParser

class BookMyShowScraper:
    """Web scraper for BookMyShow cinema pages"""
    
    def __init__(self):
        self.driver = None
        self.parser = BookMyShowParser()
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={settings.USER_AGENT}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Install ChromeDriver automatically
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _ensure_driver_alive(self):
        """Ensure the WebDriver is alive and create a new one if needed"""
        try:
            if self.driver:
                # Test if driver is still alive
                self.driver.current_url
        except (WebDriverException, Exception):
            # Driver is dead, close it and create a new one
            print("WebDriver session expired, creating new session...")
            self.close()
            self.driver = None
        
        # Create new driver if needed
        if not self.driver:
            self.driver = self._setup_driver()

    async def scrape_theater_movies(self, theater_url: str) -> Dict:
        """
        Scrape movie listings from a BookMyShow theater page
        
        Args:
            theater_url: Full BookMyShow theater URL
            
        Returns:
            Dict containing theater info and movie listings
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Parse URL to get theater info
                original_url_info = self.parser.parse_bms_url(theater_url)
                
                # Ensure driver is alive
                self._ensure_driver_alive()
                
                print(f"Scraping: {theater_url} (attempt {attempt + 1})")
                self.driver.get(theater_url)
                
                # Wait for the page to load and React components to render
                await self._wait_for_page_load()
                
                # Check if URL was redirected (date changed)
                current_url = self.driver.current_url
                redirected = False
                actual_url_info = original_url_info
                
                if current_url != theater_url:
                    try:
                        actual_url_info = self.parser.parse_bms_url(current_url)
                        # Check if the date changed
                        if actual_url_info['date'] != original_url_info['date']:
                            redirected = True
                            print(f"URL redirected - Original date: {original_url_info['date']}, Actual date: {actual_url_info['date']}")
                    except Exception as e:
                        print(f"Error parsing redirected URL: {e}")
                        # Use original URL info if parsing fails
                        actual_url_info = original_url_info
                
                # Get page source after JavaScript execution
                html_content = self.driver.page_source
                
                # Parse movie listings
                movies = self.parser.parse_movie_listings(html_content)
                
                # If redirected and no movies found, it likely means the date is invalid/not available
                if redirected and len(movies) == 0:
                    return {
                        'theater_info': original_url_info,
                        'actual_theater_info': actual_url_info,
                        'movies': movies,
                        'scraped_at': time.time(),
                        'success': False,
                        'redirected': True,
                        'error': f"Date {original_url_info['formatted_date']} is not available. BookMyShow redirected to {actual_url_info['formatted_date']}. Movies may not be opened for booking yet."
                    }
                
                return {
                    'theater_info': original_url_info,
                    'actual_theater_info': actual_url_info,
                    'movies': movies,
                    'scraped_at': time.time(),
                    'success': True,
                    'redirected': redirected
                }
                
            except WebDriverException as e:
                print(f"WebDriver error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    # Close current driver and retry
                    self.close()
                    await asyncio.sleep(2)
                    continue
                else:
                    return {
                        'theater_info': None,
                        'movies': [],
                        'error': f"WebDriver error after {max_retries} attempts: {str(e)}",
                        'success': False
                    }
            except Exception as e:
                print(f"Error scraping theater movies on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    return {
                        'theater_info': None,
                        'movies': [],
                        'error': f"Error after {max_retries} attempts: {str(e)}",
                        'success': False
                    }
        
        # This should never be reached, but just in case
        return {
            'theater_info': None,
            'movies': [],
            'error': "Unknown error occurred",
            'success': False
        }
    
    async def _wait_for_page_load(self, timeout: int = 30):
        """Wait for the page to fully load including React components"""
        try:
            # Wait for the main container to be present
            wait = WebDriverWait(self.driver, timeout)
            
            # Wait for the React virtualized container
            wait.until(
                EC.presence_of_element_located((
                    By.CLASS_NAME, "ReactVirtualized__Grid__innerScrollContainer"
                ))
            )
            
            # Additional wait for content to load
            await asyncio.sleep(3)
            
            # Check if there are movie cells
            movie_cells = self.driver.find_elements(By.CSS_SELECTOR, "[role='gridcell']")
            if not movie_cells:
                # Wait a bit more if no movies found yet
                await asyncio.sleep(5)
            
        except TimeoutException:
            print("Timeout waiting for page to load")
            # Continue anyway, might still get some content
        except Exception as e:
            print(f"Error waiting for page load: {e}")
    
    async def test_scraping(self, url: str) -> Dict:
        """Test scraping functionality with a given URL"""
        result = await self.scrape_theater_movies(url)
        return result
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

class ScrapingService:
    """Service to manage scraping operations"""
    
    def __init__(self):
        self.scraper = BookMyShowScraper()
        self.last_driver_refresh = time.time()
        self.driver_refresh_interval = 1800  # 30 minutes
    
    def _refresh_driver_if_needed(self):
        """Refresh WebDriver if it's been running for too long"""
        current_time = time.time()
        if current_time - self.last_driver_refresh > self.driver_refresh_interval:
            print("Refreshing WebDriver to prevent session expiration...")
            self.scraper.close()
            self.last_driver_refresh = current_time

    async def scrape_and_update_theater(self, theater_url: str) -> Dict:
        """
        Scrape theater data and return structured information
        """
        try:
            # Refresh driver periodically to prevent session expiration
            self._refresh_driver_if_needed()
            
            result = await self.scraper.scrape_theater_movies(theater_url)
            
            if not result['success']:
                return result
            
            # Process the data
            theater_info = result['theater_info']
            actual_theater_info = result.get('actual_theater_info', theater_info)
            movies_data = result['movies']
            redirected = result.get('redirected', False)
            
            processed_result = {
                'theater': {
                    'name': theater_info['display_name'],
                    'city': theater_info['city'],
                    'code': theater_info['theater_code'],
                    'url_path': theater_info['theater_path'],
                    'date': theater_info['date'],
                    'formatted_date': theater_info['formatted_date']
                },
                'movies': [],
                'total_movies': len(movies_data),
                'scraped_at': result['scraped_at'],
                'redirected': redirected
            }
            
            # Add actual theater info if redirected
            if redirected and actual_theater_info != theater_info:
                processed_result['actual_theater'] = {
                    'name': actual_theater_info['display_name'],
                    'city': actual_theater_info['city'],
                    'code': actual_theater_info['theater_code'],
                    'url_path': actual_theater_info['theater_path'],
                    'date': actual_theater_info['date'],
                    'formatted_date': actual_theater_info['formatted_date']
                }
            
            # Process each movie
            for movie in movies_data:
                processed_movie = {
                    'title': movie['title'],
                    'full_title': movie['full_title'],
                    'language': movie['language'],
                    'rating': movie['rating'],
                    'format_type': movie['format_type'],
                    'movie_id': movie['movie_id'],
                    'movie_url': movie['movie_url'],
                    'showtimes': movie['showtimes'],
                    'total_shows': len(movie['showtimes'])
                }
                processed_result['movies'].append(processed_movie)
            
            return {
                'success': True,
                'data': processed_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup(self):
        """Cleanup resources"""
        self.scraper.close()
