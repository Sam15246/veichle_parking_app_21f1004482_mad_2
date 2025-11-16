from app import app  # app creates and attaches .celery via make_celery
celery = app.celery  # Celery instance exposed for CLI entry points

# Usage (PowerShell / CMD):
#   (1) Start Redis:
#       redis-server
#       OR docker run -d -p 6379:6379 --name redis redis:7-alpine
#   (2) Start worker (Windows recommended pool):
#       celery -A celery_worker.celery worker -l info --pool solo
#   (3) Start beat:
#       celery -A celery_worker.celery beat -l info
# Error 10061 => Redis not running / blocked by firewall.
# Do NOT use: celery -A celery_app.make_celery ...

# Optional: allow direct python execution for quick debug
if __name__ == '__main__':
    celery.worker_main()
