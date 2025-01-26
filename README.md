# AudioSnipt

Search through YouTube videos for specific phrases and download audio clips.

## Project Structure

```
audiosnipt/
├── routes/                    # Route blueprints
│   ├── __init__.py           # Blueprint registration
│   ├── search.py             # Search and clip functionality
│   └── blog.py               # Blog routes
├── models.py                 # Database models
├── app.py                    # Main application setup
├── auth.py                   # Authentication
├── admin.py                  # Admin interface
└── stripe_webhook.py         # Payment processing
```

## Routes

### Search Routes (`/routes/search.py`)
- `POST /search` - Search for phrases in YouTube videos
  - Parameters:
    - `access_token` (optional) - Token for paid searches
    - `person_name` - Name to search for
    - `search_word` - Phrase to find
    - `sort_order` - Sort results (default: 'date')
    - `time_period` - Days to look back (default: 730)
    - `channel_id` - Specific channel to search
    - `stop_after_first` - Stop after first match

- `POST /download_clip` - Download audio clip
  - Parameters:
    - `video_id` - YouTube video ID
    - `timestamp` - Start time in seconds
    - `duration` - Clip length in seconds (default: 1.0)

- `GET /clips/<filename>` - Download generated clip file

### Blog Routes (`/routes/blog.py`)
- `GET /blog` - List all blog posts
- `GET /blog/<slug>` - View specific blog post

### Admin Routes (`/admin.py`)
- `GET /admin` - Admin dashboard
- `GET /admin/troubleshoot` - System diagnostics

### Authentication Routes (`/auth.py`)
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /logout` - Logout

### Payment Routes (`/stripe_webhook.py`)
- `POST /webhook` - Handle Stripe events
- `GET /success` - Payment success page
- `GET /cancel` - Payment cancellation page

### Core Routes (`/app.py`)
- `GET /` - Homepage
- `GET /health` - Health check endpoint
- `GET /sitemap.xml` - XML sitemap for SEO

## Authentication

The application uses Flask-Login for authentication. Admin users can be created through:
1. Environment variables (`ADMIN_EMAIL`, `ADMIN_PASSWORD`)
2. Setup token URL: `/setup-admin/<setup_token>`

## Search Tokens

Search functionality is limited by tokens:
- Free tier: 3 searches per IP address
- Paid tiers: 
  - Day pass: 50 searches
  - Week pass: 200 searches
  - Month pass: 500 searches

Tokens are formatted as: `plan_type:expiry_date:search_limit:signature`

## Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///stripe.db
STRIPE_SECRET_KEY=your_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

3. Run the application:
```bash
python app.py
```

## Deployment

The application is configured for Railway deployment with:
- Automatic HTTPS redirection
- Cloudflare proxy support
- Redis caching
- SQLite database (configurable)

## Monitoring

Health checks and monitoring available at:
- `/health` - System status
- `/admin/troubleshoot` - Detailed diagnostics

## Features

- Search through YouTube videos using person's name and specific phrases
- Case-insensitive and flexible word boundary matching
- Context display showing text before and after matches
- Download audio clips of specific moments
- Tiered access system with free and premium options
- User-friendly web interface
- Secure HTTPS access via Cloudflare
- Automatic domain handling and redirects

## System Architecture

### Core Components

1. **Web Interface** (`templates/index.html`)
   - Bootstrap 5.1.3 for styling
   - Font Awesome 6.0.0 for icons
   - Client-side JavaScript for form handling and UI updates
   - Responsive design for mobile and desktop

2. **Backend Server** (`app.py`, `youtube_search_and_clip.py`)
   - Flask web framework with Gunicorn
   - YouTube Data API integration
   - Audio processing capabilities
   - Token-based access control
   - Rate limiting with Redis
   - SQLAlchemy for database management

### External Services

- **YouTube Data API**: For video search and metadata
- **YouTube Transcript API**: For accessing video captions
- **Stripe**: Payment processing and subscription management
- **Railway**: Hosting and deployment platform
- **Cloudflare**: DNS, SSL, and CDN services

## Dependencies

### Python Packages
```
Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
google-api-python-client==2.108.0
youtube-transcript-api==0.6.1
python-dotenv==1.0.0
yt-dlp==2023.12.30
ffmpeg-python==0.2.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Limiter==3.5.0
stripe==7.10.0
```

### System Requirements
- Python 3.11+
- FFmpeg (for audio processing)
- YouTube API Key
- Stripe API Keys (public and secret)
- Redis (optional, for rate limiting)

## File Structure

```
├── app.py                      # Main Flask application
├── youtube_search_and_clip.py  # Core search and clip functionality
├── auth.py                     # Authentication handling
├── admin.py                    # Admin interface
├── models.py                   # Database models
├── notifications.py            # Email notifications
├── subscription_utils.py       # Subscription handling
├── stripe_webhook.py          # Stripe webhook handling
├── requirements.txt           # Python dependencies
├── railway.toml              # Railway deployment config
├── .env                      # Environment variables
├── templates/
│   ├── index.html           # Main interface
│   └── admin/               # Admin templates
├── static/                  # Static assets
├── clips/                   # Generated audio clips
└── search_debug.log        # Debug logging
```

## Module Functions

### youtube_search_and_clip.py

1. **Search Implementation**
   - Flexible phrase matching with context
   - Multiple search strategies (exact, fuzzy, phonetic)
   - Transcript combination for better matches
   - Detailed logging for debugging

2. **Audio Processing**
   - Efficient clip extraction
   - Format conversion handling
   - Error recovery

### Web Application (app.py)

1. **Request Handling**
   - Cloudflare proxy support
   - Domain redirection
   - Rate limiting
   - Session management

2. **Security Features**
   - HTTPS enforcement
   - XSS protection
   - CSRF protection
   - Secure cookie handling

## Environment Variables

Required in `.env` file:
```
YOUTUBE_API_KEY=your_youtube_api_key
FLASK_SECRET_KEY=your_secret_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
DOMAIN=audiosnipt.com
FLASK_ENV=production
```

## Deployment

1. **Railway Configuration**
   ```toml
   [build]
   builder = "NIXPACKS"
   buildCommand = "pip install -r requirements.txt"
   pythonVersion = "3.11"

   [deploy]
   startCommand = "gunicorn app:app --timeout 300 --workers 4 --bind 0.0.0.0:$PORT"
   restartPolicyType = "ON_FAILURE"
   restartPolicyMaxRetries = 10

   [nixpacks]
   runtime = "python"
   packages = ["ffmpeg"]
   ```

2. **DNS Configuration (Cloudflare)**
   ```
   CNAME  audiosnipt.com    [railway-domain].up.railway.app
   CNAME  www              [railway-domain].up.railway.app
   ```

3. **SSL/TLS Settings**
   - Mode: Full
   - Always Use HTTPS: Enabled
   - Min TLS Version: 1.2
   - Automatic HTTPS Rewrites: Enabled

## Security Considerations

1. **Domain Security**
   - Cloudflare proxy protection
   - HTTPS enforcement
   - Proper redirect handling
   - Secure cookie configuration

2. **Rate Limiting**
   - Per-IP limits
   - Configurable thresholds
   - Redis-backed storage

3. **Access Control**
   - Role-based permissions
   - Subscription validation
   - Token verification

## Feature Implementation Details

### Search Algorithm

1. **Enhanced Matching**
   - Multiple matching strategies
   - Context window optimization
   - Duplicate filtering
   - Performance logging

2. **Error Handling**
   - Graceful degradation
   - Detailed error messages
   - Recovery mechanisms

### Subscription System

1. **Access Tiers**
   - Free: 3 searches
   - Day Pass: 50 searches ($2)
   - Week Pass: 200 searches ($5)
   - Month Pass: 500 searches ($10)

2. **Payment Processing**
   - Secure Stripe integration
   - Webhook handling
   - Subscription management
   - Payment recovery

## Troubleshooting

### Common Issues

1. **DNS and Domain**
   - Check Cloudflare proxy status
   - Verify DNS propagation
   - Review redirect loops
   - Check SSL/TLS settings

2. **Application Errors**
   - Check application logs
   - Review search_debug.log
   - Monitor Railway status
   - Verify environment variables

### Monitoring

1. **Performance Metrics**
   - Response times
   - Error rates
   - API quotas
   - Resource usage

2. **Health Checks**
   - `/health` endpoint monitoring
   - Database connectivity
   - External service status
   - Resource availability

## Support

For issues and support:
1. Check the troubleshooting guide
2. Review application logs
3. Submit detailed issue reports with:
   - Error messages
   - Log excerpts
   - Steps to reproduce
   - Environment details

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with:
   - Clear description
   - Test coverage
   - Documentation updates #   a u d i o  
 