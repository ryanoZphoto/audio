from datetime import datetime
from flask import request
from app.extensions import db
from app.models import Visit

class AnalyticsMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Record start time
        start_time = datetime.utcnow()
        
        def analytics_start_response(status, headers, exc_info=None):
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            try:
                # Create visit record
                visit = Visit(
                    path=environ.get('PATH_INFO'),
                    ip_address=environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR')),
                    user_agent=environ.get('HTTP_USER_AGENT'),
                    http_method=environ.get('REQUEST_METHOD'),
                    status_code=int(status.split()[0]),
                    response_time=response_time,
                    referrer=environ.get('HTTP_REFERER'),
                )
                db.session.add(visit)
                db.session.commit()
            except Exception as e:
                print(f"Analytics error: {str(e)}")
            
            return start_response(status, headers, exc_info)
        
        return self.app(environ, analytics_start_response) 