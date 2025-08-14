# FILE: logs/apps.py

from django.apps import AppConfig
<<<<<<< HEAD
=======
import sys
>>>>>>> e868661 (Final project version with Docker setup)

class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs'

<<<<<<< HEAD
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
=======
    def ready(self):
        # --- MODIFIED: Check for 'gunicorn' to start the scheduler ---
        # This prevents it from running during 'migrate' or other commands.
        is_gunicorn = "gunicorn" in sys.argv[0]

        if is_gunicorn:
            from . import jobs
            from apscheduler.schedulers.background import BackgroundScheduler
            from django_apscheduler.jobstores import DjangoJobStore

            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), "default")
            
            scheduler.add_job(
                jobs.weekly_maintenance_check,
                trigger='cron',
                day_of_week='mon',
                hour='2',
                minute='0',
                id='weekly_maintenance_check',
                replace_existing=True,
            )
            
            try:
                print("Starting scheduler...")
                scheduler.start()
            except Exception as e:
                print(f"Scheduler failed to start: {e}")
                pass
>>>>>>> e868661 (Final project version with Docker setup)
