from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from django_apscheduler.jobstores import DjangoJobStore, register_events

import sys

def get_releases_and_create_results():
    ...

def check_the_need_to_calculate_releases():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        get_releases_and_create_results, 
        trigger=CronTrigger(
            hour=00,
            minute=00,
        ),
        name='get_releases_and_create_results', 
        jobstore='default',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=10,
        coalesce= True,
        id='get_releases_and_create_results',
    )
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
