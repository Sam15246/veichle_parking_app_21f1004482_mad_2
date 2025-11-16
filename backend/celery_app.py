from celery import Celery

def make_celery(flask_app):
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config['CELERY_BROKER_URL'],
        backend=flask_app.config['CELERY_RESULT_BACKEND'],
        include=['tasks']
    )
    celery.conf.update(timezone='UTC', enable_utc=True, beat_schedule=flask_app.config.get('CELERY_BEAT_SCHEDULE', {}))

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery  # Use app.celery (created in app.py), not this factory in -A argument.
