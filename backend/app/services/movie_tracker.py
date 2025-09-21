from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from datetime import datetime, date
from app.models import Movie, Showtime, Theater, UserSubscription, Notification, User
from app.services.scraper import ScrapingService
import asyncio

class MovieComparisonService:
    """Service to compare movie data and detect changes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scraping_service = ScrapingService()
    
    def find_matching_movies(self, search_term: str, movies: List[Dict], threshold: int = 70) -> List[Dict]:
        """
        Find movies that match the search term using fuzzy matching
        
        Args:
            search_term: User's search term (can be partial)
            movies: List of movie dictionaries
            threshold: Minimum similarity score (0-100)
            
        Returns:
            List of matching movies with similarity scores
        """
        matches = []
        
        for movie in movies:
            # Compare with both title and full_title
            title_score = fuzz.partial_ratio(search_term.lower(), movie['title'].lower())
            full_title_score = fuzz.partial_ratio(search_term.lower(), movie['full_title'].lower())
            
            # Use the higher score
            max_score = max(title_score, full_title_score)
            
            if max_score >= threshold:
                movie_copy = movie.copy()
                movie_copy['similarity_score'] = max_score
                matches.append(movie_copy)
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches
    
    def compare_movie_data(self, old_movies: List[Dict], new_movies: List[Dict]) -> Dict:
        """
        Compare old and new movie data to detect changes
        
        Returns:
            Dict with added_movies, removed_movies, and updated_showtimes
        """
        old_movies_dict = {movie['title']: movie for movie in old_movies}
        new_movies_dict = {movie['title']: movie for movie in new_movies}
        
        old_titles = set(old_movies_dict.keys())
        new_titles = set(new_movies_dict.keys())
        
        # Find added and removed movies
        added_movies = []
        for title in new_titles - old_titles:
            added_movies.append(new_movies_dict[title])
        
        removed_movies = []
        for title in old_titles - new_titles:
            removed_movies.append(old_movies_dict[title])
        
        # Find movies with updated showtimes
        updated_showtimes = []
        for title in old_titles & new_titles:
            old_movie = old_movies_dict[title]
            new_movie = new_movies_dict[title]
            
            old_times = set(show['time'] for show in old_movie['showtimes'])
            new_times = set(show['time'] for show in new_movie['showtimes'])
            
            if old_times != new_times:
                added_times = new_times - old_times
                removed_times = old_times - new_times
                
                if added_times or removed_times:
                    updated_showtimes.append({
                        'movie': new_movie,
                        'added_times': list(added_times),
                        'removed_times': list(removed_times)
                    })
        
        return {
            'added_movies': added_movies,
            'removed_movies': removed_movies,
            'updated_showtimes': updated_showtimes
        }
    
    async def check_subscriptions_and_notify(self, theater_id: int, target_date: date, new_data: Dict):
        """
        Check active subscriptions and send notifications for changes
        """
        # Get active subscriptions for this theater and date
        subscriptions = self.db.query(UserSubscription).filter(
            UserSubscription.theater_id == theater_id,
            UserSubscription.target_date == target_date,
            UserSubscription.is_active == True
        ).all()
        
        if not subscriptions:
            return
        
        # Get current movie data from database
        current_movies = self.get_current_movies(theater_id, target_date)
        
        # Compare data
        changes = self.compare_movie_data(current_movies, new_data['movies'])
        
        # Process notifications for each subscription
        for subscription in subscriptions:
            await self._process_subscription_notifications(subscription, changes)
    
    async def _process_subscription_notifications(self, subscription: UserSubscription, changes: Dict):
        """Process notifications for a single subscription"""
        user = subscription.user
        theater = subscription.theater
        movie_name = subscription.movie_name
        
        notifications_to_create = []
        
        # Check for new movies matching the subscription
        if subscription.notify_new_shows and changes['added_movies']:
            matching_movies = self.find_matching_movies(movie_name, changes['added_movies'])
            
            for movie in matching_movies:
                message = self._create_new_movie_message(movie, theater, subscription.target_date)
                notifications_to_create.append({
                    'user_id': user.id,
                    'message': message,
                    'notification_type': 'new_movie'
                })
        
        # Check for new showtimes for existing movies
        if subscription.notify_new_times and changes['updated_showtimes']:
            for update in changes['updated_showtimes']:
                if update['added_times']:
                    # Check if this movie matches the subscription
                    matches = self.find_matching_movies(movie_name, [update['movie']])
                    if matches:
                        message = self._create_new_showtime_message(
                            update['movie'], 
                            update['added_times'], 
                            theater, 
                            subscription.target_date
                        )
                        notifications_to_create.append({
                            'user_id': user.id,
                            'message': message,
                            'notification_type': 'new_showtime'
                        })
        
        # Create notifications in database
        for notif_data in notifications_to_create:
            notification = Notification(**notif_data)
            self.db.add(notification)
        
        # If notifications were created, deactivate the subscription (auto-unsubscribe)
        if notifications_to_create:
            subscription.is_active = False
            subscription.deactivated_reason = 'notification_sent'
            subscription.deactivated_at = datetime.now()
            
            print(f"Auto-unsubscribed user {user.id} from '{movie_name}' at {theater.name} after sending notification")
            self.db.commit()
    
    def _create_new_movie_message(self, movie: Dict, theater: Theater, target_date: date) -> str:
        """Create notification message for new movie"""
        showtimes_str = ", ".join([show['time'] for show in movie['showtimes']])
        
        message = f"🎬 Movie Alert!\n\n"
        message += f"'{movie['title']}' is now available at {theater.name}\n"
        message += f"Date: {target_date.strftime('%B %d, %Y')}\n"
        message += f"Language: {movie['language']}\n"
        message += f"Rating: {movie['rating']}\n"
        message += f"Showtimes: {showtimes_str}\n\n"
        message += f"Book now on BookMyShow!\n\n"
        message += f"✅ Your subscription has been automatically stopped since the movie is now available."
        
        return message
    
    def _create_new_showtime_message(self, movie: Dict, new_times: List[str], theater: Theater, target_date: date) -> str:
        """Create notification message for new showtimes"""
        times_str = ", ".join(new_times)
        
        message = f"🆕 New Show Added!\n\n"
        message += f"'{movie['title']}' - New showtimes: {times_str}\n"
        message += f"Theater: {theater.name}\n"
        message += f"Date: {target_date.strftime('%B %d, %Y')}\n\n"
        message += f"Book now on BookMyShow!\n\n"
        message += f"✅ Your subscription has been automatically stopped since new shows are now available."
        
        return message
    
    def get_current_movies(self, theater_id: int, target_date: date) -> List[Dict]:
        """Get current movies from database for comparison"""
        movies = self.db.query(Movie).filter(
            Movie.theater_id == theater_id,
            Movie.show_date == target_date
        ).all()
        
        result = []
        for movie in movies:
            movie_dict = {
                'title': movie.title,
                'full_title': f"{movie.title} ({movie.rating})" if movie.rating else movie.title,
                'language': movie.language,
                'rating': movie.rating,
                'format_type': movie.format_type,
                'movie_id': movie.bms_movie_id,
                'movie_url': movie.bms_url_path,
                'showtimes': []
            }
            
            # Add showtimes
            for showtime in movie.showtimes:
                movie_dict['showtimes'].append({
                    'time': showtime.show_time,
                    'screen_type': showtime.screen_type
                })
            
            result.append(movie_dict)
        
        return result
    
    def update_database_with_new_data(self, theater_id: int, target_date: date, movies_data: List[Dict]):
        """Update database with new movie data"""
        try:
            # Remove existing data for this theater/date
            existing_movies = self.db.query(Movie).filter(
                Movie.theater_id == theater_id,
                Movie.show_date == target_date
            ).all()
            
            for movie in existing_movies:
                self.db.delete(movie)
            
            # Add new data
            for movie_data in movies_data:
                movie = Movie(
                    title=movie_data['title'],
                    language=movie_data['language'],
                    rating=movie_data['rating'],
                    format_type=movie_data['format_type'],
                    bms_movie_id=movie_data['movie_id'],
                    bms_url_path=movie_data['movie_url'],
                    show_date=target_date,
                    theater_id=theater_id
                )
                
                self.db.add(movie)
                self.db.flush()  # Get the movie ID
                
                # Add showtimes
                for showtime_data in movie_data['showtimes']:
                    showtime = Showtime(
                        movie_id=movie.id,
                        show_time=showtime_data['time'],
                        screen_type=showtime_data['screen_type']
                    )
                    self.db.add(showtime)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating database: {e}")
            return False
