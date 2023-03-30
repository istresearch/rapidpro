import logging

from temba.utils.celery import nonoverlapping_task

from .cto import export_cto_msgs

logger = logging.getLogger(__name__)

@nonoverlapping_task(track_started=True, name="export_cto_msgs", lock_timeout=3600)
def export_cto_msgs_task():
    logger.info("Starting export_cto_msgs task")
    export_cto_msgs()
    logger.info("Completed export_cto_msgs task")
