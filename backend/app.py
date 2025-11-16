from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import redis
from celery_app import make_celery
from models import db, init_sample_data, Admin
from routes import api
from celery.schedules import crontab  # added

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'  # Change this in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # For development, tokens don't expire
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "parking_system.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Redis configuration (env override supported)
    app.config.setdefault('REDIS_HOST', '127.0.0.1')
    app.config.setdefault('REDIS_PORT', 6379)
    app.config.setdefault('REDIS_DB', 0)
    redis_url = os.getenv('REDIS_URL')  # e.g., redis://127.0.0.1:6379/0

    # Celery configuration (broker/result from REDIS_URL if provided)
    if redis_url:
        app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', redis_url.replace('/0', '/1'))
        app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', redis_url.replace('/0', '/2'))
    else:
        app.config.setdefault('CELERY_BROKER_URL', f"redis://{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}/1")
        app.config.setdefault('CELERY_RESULT_BACKEND', f"redis://{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}/2")

    # Celery beat: switch to crontab schedules (daily at 18:00, monthly on 1st at 08:00)
    app.config['CELERY_BEAT_SCHEDULE'] = {
        'daily-reminders': {
            'task': 'tasks.send_daily_reminders',
            'schedule': crontab(hour=18, minute=0),
        },
        'monthly-reports': {
            'task': 'tasks.generate_monthly_reports',
            'schedule': crontab(day_of_month='1', hour=8, minute=0),
        }
    }
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    api.init_app(app)
    app.celery = make_celery(app)

    # Redis client (graceful fallback; supports REDIS_URL)
    try:
        if redis_url:
            app.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            app.redis = redis.Redis(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                db=app.config['REDIS_DB'],
                decode_responses=True
            )
        app.redis.ping()
        print("[INFO] Redis connected; caching enabled")
    except Exception as e:
        app.redis = None
        print(f"[WARN] Redis not available, caching disabled. Reason: {e}")

    # Cache TTLs (seconds) and limits
    app.config['LOTS_CACHE_TTL'] = int(os.getenv('LOTS_CACHE_TTL', '60'))
    app.config['ANALYTICS_CACHE_TTL'] = int(os.getenv('ANALYTICS_CACHE_TTL', '120'))
    app.config['MAX_ACTIVE_RESERVATIONS_PER_USER'] = int(os.getenv('MAX_ACTIVE_RESERVATIONS_PER_USER', '5'))
    return app

app = create_app()

@app.route('/')
def home():
    return {
        'message': 'Vehicle Parking System API', 
        'status': 'running',
        'version': '1.0.0'
    }

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'database': 'connected'}

# New ops endpoint to verify Redis & Celery config quickly
@app.route('/ops/status')
def ops_status():
    redis_ok = False
    try:
        if getattr(app, 'redis', None):
            app.redis.ping()
            redis_ok = True
    except Exception:
        redis_ok = False
    return {
        'redis': {
            'enabled': getattr(app, 'redis', None) is not None,
            'ok': redis_ok,
            'url': os.getenv('REDIS_URL') or f"redis://{app.config.get('REDIS_HOST')}:{app.config.get('REDIS_PORT')}/{app.config.get('REDIS_DB')}"
        },
        'celery': {
            'broker': app.config.get('CELERY_BROKER_URL'),
            'backend': app.config.get('CELERY_RESULT_BACKEND'),
            'beat_schedule': True
        }
    }, 200

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Initialize sample data
        print("Initializing sample data...")
        init_sample_data()
        
        print("Database setup completed successfully!")
        print("=" * 50)
        print("Admin Login Credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("=" * 50)
        
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
