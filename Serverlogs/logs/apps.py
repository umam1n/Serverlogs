# FILE: logs/apps.py

from django.apps import AppConfig

class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs'

    # Add the ready method
    def ready(self):
        from . import jobs  # Import your jobs file
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Schedule the job to run every Monday at 2 AM
        scheduler.add_job(
            jobs.weekly_maintenance_check,
            trigger='cron',
            day_of_week='mon',
            hour='2',
            minute='0',
            id='weekly_maintenance_check',  # A unique ID for this job
            replace_existing=True,
        )
        
        try:
            print("Starting scheduler...")
            scheduler.start()
        except Exception as e:
            print(f"Scheduler failed to start: {e}")
            # This can happen if you run makemigrations before the scheduler table exists
            pass