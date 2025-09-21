# BookMyShow Movie Tracker

A real-time movie show tracker that monitors BookMyShow for new shows and sends notifications via Telegram when movies become available or new showtimes are added.

## Features

- **Real-time Monitoring**: Checks every 2 minutes for new movies and showtimes
- **Smart Movie Matching**: Partial name matching (e.g., "Demon Slayer" matches "Demon Slayer: Kimetsu no Yaiba Infinity Castle")
- **Telegram Notifications**: Instant notifications when movies become available or new shows are added
- **URL Parsing**: Automatically extracts theater and date information from BookMyShow URLs
- **Web Interface**: Modern React frontend for managing subscriptions
- **Test Scraping**: Built-in tool to test scraping functionality

## Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - Database ORM
- **Selenium** - Web scraping with Chrome WebDriver
- **BeautifulSoup** - HTML parsing
- **python-telegram-bot** - Telegram integration
- **SQLite** - Database (easily switchable to PostgreSQL)

### Frontend
- **React 18** - UI framework
- **Tailwind CSS** - Styling
- **React Query** - Data fetching and caching
- **React Hook Form** - Form handling
- **Lucide React** - Icons

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Chrome browser (for Selenium)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd book-my-show-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Create Telegram Bot**
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the bot token to your `.env` file

6. **Run the backend**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000` and the backend API at `http://localhost:8000`.

## Usage

### Web Interface

1. **Home Page**: Enter a BookMyShow URL to create a subscription
2. **Subscriptions**: View and manage your active subscriptions
3. **Test Scraping**: Test the scraping functionality with any URL

### URL Format

BookMyShow URLs should follow this format:
```
https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924
```

Where:
- `hyderabad` = City
- `prasads-multiplex-hyderabad` = Theater name
- `PRHN` = Theater code
- `20250924` = Date (YYYYMMDD format)

### Creating a Subscription

1. Paste a BookMyShow theater URL
2. Confirm theater and date information
3. Enter the movie name (partial matching supported)
4. Provide your Telegram ID (get it from @userinfobot)
5. Choose notification preferences

### Telegram Commands

- `/start` - Initialize the bot
- `/help` - Show help information
- `/subscribe` - Create a new subscription
- `/list` - View your subscriptions
- `/unsubscribe <ID>` - Remove a subscription

## API Endpoints

### Subscriptions
- `POST /api/v1/subscriptions/parse-url` - Parse BookMyShow URL
- `POST /api/v1/subscriptions/create` - Create subscription
- `GET /api/v1/subscriptions/user/{telegram_id}` - Get user subscriptions
- `DELETE /api/v1/subscriptions/{id}` - Delete subscription
- `POST /api/v1/subscriptions/test-scraping` - Test scraping

### Theaters
- `GET /api/v1/theaters/search` - Search theaters
- `GET /api/v1/theaters/{id}` - Get theater details

### Movies
- `GET /api/v1/movies/theater/{theater_id}` - Get movies by theater
- `GET /api/v1/movies/search` - Search movies

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./bookmyshow_tracker.db` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required for notifications |
| `SCRAPING_INTERVAL_MINUTES` | How often to check for updates | `2` |
| `USER_AGENT` | User agent for web scraping | Chrome user agent |
| `SECRET_KEY` | Security key | Change in production |

### Database Schema

The system uses the following main tables:
- `users` - User information and Telegram IDs
- `theaters` - Theater information and BookMyShow codes
- `movies` - Movie listings with showtimes
- `user_subscriptions` - User movie tracking subscriptions
- `notifications` - Notification queue and history

## How It Works

1. **URL Parsing**: Extracts theater and date from BookMyShow URLs
2. **Web Scraping**: Uses Selenium to load pages and BeautifulSoup to parse HTML
3. **Data Comparison**: Compares new data with stored data to detect changes
4. **Smart Matching**: Uses fuzzy string matching to find movies by partial names
5. **Notifications**: Sends Telegram messages for new movies or showtimes
6. **Scheduling**: Runs checks every 2 minutes for active subscriptions

## Deployment

### Production Setup

1. **Use PostgreSQL** instead of SQLite:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost/bookmyshow_tracker
   ```

2. **Set up reverse proxy** (nginx):
   ```nginx
   location /api/ {
       proxy_pass http://localhost:8000/api/;
   }
   
   location / {
       proxy_pass http://localhost:3000/;
   }
   ```

3. **Use process manager** (PM2, systemd, or Docker)

4. **Set up monitoring** and logging

### Docker Deployment

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/bookmyshow
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=bookmyshow
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

1. **Chrome WebDriver Issues**
   - Install Chrome browser
   - Update Chrome to latest version
   - Check if webdriver-manager can download ChromeDriver

2. **Telegram Bot Not Responding**
   - Verify bot token in `.env`
   - Check if bot is started with `/start` command
   - Ensure webhook is not set (use polling mode)

3. **Scraping Failures**
   - BookMyShow may have changed their HTML structure
   - Check if the URL format is correct
   - Verify network connectivity

4. **Database Errors**
   - Check database permissions
   - Verify DATABASE_URL format
   - Run database migrations if needed

### Logs

Check logs for debugging:
- Backend logs: Console output from uvicorn
- Scraping logs: Check scheduler service logs
- Database logs: SQLAlchemy logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Please respect BookMyShow's terms of service and implement appropriate rate limiting and ethical scraping practices.
