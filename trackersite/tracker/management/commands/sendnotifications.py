from django.core.management.base import NoArgsCommand
from tracker.models import Notification
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.utils import translation
from django.utils.html import strip_tags

class Command(NoArgsCommand):
    help = 'Process pending notifications'
    
    def handle_noargs(self, **options):
        translation.activate('cs_CZ')
        subject_text = get_template('notification/notification_subject.txt').render()
        html_template = get_template('notification/notification_html.html')
        for user in User.objects.all():
            if len(Notification.objects.filter(target_user=user)) > 0:
                c_dict = {
                    "ack_notifs": Notification.objects.filter(target_user=user, notification_type__in=["ack", "ack_remove"]),
                    "ticket_new_notifs": Notification.objects.filter(target_user=user, notification_type="ticket_new"),
                    "comment_notifs": Notification.objects.filter(target_user=user, notification_type="comment")
                }
                c = Context(c_dict)
                user.email_user(subject_text, strip_tags(html_template.render(c)), html_message=html_template.render(c))
            for notification in Notification.objects.filter(target_user=user):
                notification.delete()