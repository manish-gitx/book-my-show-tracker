from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class BookMyShowParser:
    """Parser for BookMyShow HTML content and URLs"""
    
    @staticmethod
    def parse_bms_url(url: str) -> Dict[str, str]:
        """
        Parse BookMyShow URL to extract theater and date information
        Example: https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924
        Returns: {
            'theater_path': 'hyderabad/prasads-multiplex-hyderabad',
            'theater_code': 'PRHN',
            'date': '20250924',
            'city': 'hyderabad',
            'theater_name': 'prasads-multiplex-hyderabad'
        }
        """
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) < 6 or 'cinemas' not in path_parts:
                raise ValueError("Invalid BookMyShow cinema URL format")
            
            # Extract components
            cinemas_index = path_parts.index('cinemas')
            city = path_parts[cinemas_index + 1]
            theater_name = path_parts[cinemas_index + 2]
            theater_code = path_parts[cinemas_index + 4]  # After 'buytickets'
            date = path_parts[cinemas_index + 5]
            
            theater_path = f"{city}/{theater_name}"
            
            # Format theater name for display
            display_name = theater_name.replace('-', ' ').title()
            
            return {
                'theater_path': theater_path,
                'theater_code': theater_code,
                'date': date,
                'city': city,
                'theater_name': theater_name,
                'display_name': display_name,
                'formatted_date': BookMyShowParser.format_date(date)
            }
        except Exception as e:
            raise ValueError(f"Failed to parse BookMyShow URL: {str(e)}")
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Convert YYYYMMDD to readable format"""
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%B %d, %Y')
        except ValueError:
            return date_str
    
    @staticmethod
    def parse_movie_listings(html_content: str) -> List[Dict]:
        """
        Parse the HTML content to extract movie listings and showtimes
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        movies = []
        
        # Find the main container
        main_container = soup.find('div', {'class': 'ReactVirtualized__Grid__innerScrollContainer'})
        if not main_container:
            return movies
        
        # Find all movie entries (gridcells)
        movie_cells = main_container.find_all('div', {'role': 'gridcell'})
        
        for cell in movie_cells:
            try:
                movie_data = BookMyShowParser._parse_single_movie(cell)
                if movie_data:
                    movies.append(movie_data)
            except Exception as e:
                print(f"Error parsing movie cell: {e}")
                continue
        
        return movies
    
    @staticmethod
    def _parse_single_movie(cell) -> Optional[Dict]:
        """Parse a single movie cell to extract movie information"""
        try:
            movie_container = cell.find('div', class_='sc-1412vr2-0')
            if not movie_container:
                return None
            
            # Extract movie title and link
            title_link = movie_container.find('a', class_='sc-1412vr2-2')
            if not title_link:
                return None
            
            title = title_link.get_text().strip()
            movie_url = title_link.get('href', '')
            
            # Extract movie ID from URL
            movie_id_match = re.search(r'/ET(\d+)', movie_url)
            movie_id = movie_id_match.group(0) if movie_id_match else None
            
            # Extract rating from title (e.g., "Movie Name (UA13+)")
            rating_match = re.search(r'\(([^)]+)\)$', title)
            rating = rating_match.group(1) if rating_match else None
            clean_title = re.sub(r'\s*\([^)]+\)$', '', title).strip()
            
            # Extract language and format
            language_container = movie_container.find('div', class_='sc-1412vr2-4')
            language = None
            format_type = None
            
            if language_container:
                language_link = language_container.find('a', class_='sc-1412vr2-5')
                if language_link:
                    language = language_link.get_text().strip()
                
                format_span = language_container.find('span', class_='sc-1412vr2-6')
                if format_span:
                    format_text = format_span.get_text().strip()
                    format_type = format_text.replace(',', '').strip()
            
            # Extract showtimes
            showtimes = BookMyShowParser._parse_showtimes(movie_container)
            
            return {
                'title': clean_title,
                'full_title': title,
                'rating': rating,
                'language': language,
                'format_type': format_type,
                'movie_url': movie_url,
                'movie_id': movie_id,
                'showtimes': showtimes
            }
            
        except Exception as e:
            print(f"Error parsing single movie: {e}")
            return None
    
    @staticmethod
    def _parse_showtimes(movie_container) -> List[Dict]:
        """Extract showtimes from a movie container"""
        showtimes = []
        
        # Find showtimes container
        showtimes_container = movie_container.find('div', class_='sc-19dkgz1-0')
        if not showtimes_container:
            return showtimes
        
        # Find all showtime entries
        showtime_entries = showtimes_container.find_all('div', class_='sc-1skzbbo-0')
        
        for entry in showtime_entries:
            try:
                # Find time
                time_span = entry.find('span', class_='sc-yr56qh-1')
                if not time_span:
                    continue
                
                show_time = time_span.get_text().strip()
                
                # Find screen type (optional)
                screen_span = entry.find('span', class_='sc-yr56qh-2')
                screen_type = screen_span.get_text().strip() if screen_span else None
                
                showtimes.append({
                    'time': show_time,
                    'screen_type': screen_type
                })
                
            except Exception as e:
                print(f"Error parsing showtime: {e}")
                continue
        
        return showtimes
