from celery import shared_task
from django.core.mail import send_mail
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind = True, max_retries = 3)
def task_send_verification_email(self,user_email,verification_url):
       try:
              subject = "Verify you email"
              message = f"Click here: {verification_url}"
              from_email =  settings.DEFAULT_FROM_EMAIL
              recipient_list = [user_email]
              send_mail(subject,message,from_email,recipient_list)
              return f"verification sent to {user_email}"

       except Exception as exc:
              logger.error(f"Faild to verification email for {user_email}: {exc}")
              raise self.retry(exc = exc, countdown = 60)
