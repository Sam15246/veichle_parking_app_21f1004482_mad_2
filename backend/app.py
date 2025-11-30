from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import redis
from celery_app import make_celery
from models import db, init_sample_data
from celery.schedules import crontab
from flask import g
from datetime import timedelta
def create_app():
    app = Flask(__name__)
    CORS(app)
    # Load environment variables from .env for SMTP and other configs
    try:
        load_dotenv()
    except Exception:
        pass

    # Core config (use environment with safe defaults for dev)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    jwt_hours = int(os.getenv('JWT_EXPIRES_HOURS', '24'))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=jwt_hours)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "parking_system.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------------
    # 2. Redis config
    # -------------------------------
    app.config.setdefault('REDIS_HOST', '127.0.0.1')
    app.config.setdefault('REDIS_PORT', 6379)
    app.config.setdefault('REDIS_DB', 0)

    redis_url = os.getenv('REDIS_URL')

    # -------------------------------
    # 3. Celery config
    # -------------------------------
    if redis_url:
        app.config['CELERY_BROKER_URL'] = redis_url.replace('/0', '/1')
        app.config['CELERY_RESULT_BACKEND'] = redis_url.replace('/0', '/2')
    else:
        app.config['CELERY_BROKER_URL'] = f"redis://127.0.0.1:6379/1"
        app.config['CELERY_RESULT_BACKEND'] = f"redis://127.0.0.1:6379/2"

    # Celery beat schedule
    app.config['CELERY_BEAT_SCHEDULE'] = {
        'daily-reminders': {
            'task': 'tasks.send_daily_reminders',
            'schedule': crontab(minute=0, hour=9),
        },
        'monthly-reports': {
            'task': 'tasks.generate_monthly_reports',
            'schedule': crontab(minute=15, hour=9, day_of_month='1'),
        }
    }

    # Cache TTLs (in seconds)
    app.config['LOTS_CACHE_TTL'] = 30  # 30 seconds
    app.config['ANALYTICS_CACHE_TTL'] = 60  # 60 seconds
    app.config['MAX_ACTIVE_RESERVATIONS_PER_USER'] = 5 # New config

    # -------------------------------
    # 4. Init DB + JWT
    # -------------------------------
    db.init_app(app)
    JWTManager(app)

    # -------------------------------
    # 5. INIT CELERY FIRST
    # -------------------------------
    celery_config = {
        'broker_url': app.config['CELERY_BROKER_URL'],
        'result_backend': app.config['CELERY_RESULT_BACKEND'],
        'beat_schedule': app.config['CELERY_BEAT_SCHEDULE'],
    }
    app.celery = make_celery(app, celery_config)

    # Import routes after app and celery initialization
    from routes import api
    api.init_app(app)

    # -------------------------------
    # 7. Init Redis client
    # -------------------------------
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
        print("[WARN] Redis not available:", e)
        app.redis = None

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

# Ops endpoint to verify Redis & Celery config
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

# Inject cache headers for visibility on cached endpoints
@app.after_request
def add_cache_headers(response):
    try:
        cache_hit = getattr(g, 'cache_hit', None)
        cache_key = getattr(g, 'cache_key', None)
        ttl = getattr(g, 'cache_ttl', None)
        if cache_hit is not None:
            response.headers['X-Cache'] = 'HIT' if cache_hit else 'MISS'
        if cache_key:
            response.headers['X-Cache-Key'] = cache_key
        if ttl is not None:
            response.headers['X-Cache-TTL'] = str(ttl)
    except Exception:
        # Do not break response flow if header injection fails
        pass
    return response

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