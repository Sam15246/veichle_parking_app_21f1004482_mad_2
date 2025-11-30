from celery import Celery

def make_celery(app, config):
    celery = Celery(app.import_name)
    # Apply explicit config (broker_url/result_backend/beat_schedule, etc.)
    celery.conf.update(config)
    # Make this the default Celery app so @shared_task binds correctly
    celery.set_default()

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
