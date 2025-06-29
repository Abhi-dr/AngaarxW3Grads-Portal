from celery import shared_task
import subprocess
import logging

logger = logging.getLogger(__name__)

@shared_task
def backup_database():
    """
    Task to back up the database using Django's dbbackup command.
    """
    try:
        result = subprocess.run(
            ['sudo', 'python3', 'manage.py', 'dbbackup'],
            check=True,
            text=True,
            capture_output=True
        )
        logger.info("Database backup completed successfully: %s", result.stdout)
        return "Database backup completed successfully."
    except subprocess.CalledProcessError as e:
        logger.error("Database backup failed: %s", e.stderr)
        raise e
