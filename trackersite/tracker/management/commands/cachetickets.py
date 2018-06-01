from django.core.management.base import NoArgsCommand
from django.conf import settings
import os.path
import json
from tracker.models import Ticket

class Command(NoArgsCommand):
    help = 'Cache tickets'
    
    def handle_noargs(self, **options):
        tickets = []
        for ticket in Ticket.objects.order_by('-id'):
            tickets.append({
                "pk": '<a href="%s">%s</a>' % (ticket.get_absolute_url(), ticket.pk),
                "event_date": unicode(ticket.event_date),
                "summary": '<a class="ticket-summary" href="%s">%s</a>' % (ticket.get_absolute_url(), ticket.summary),
                "grant": '<a href="%s">%s</a>' % (ticket.topic.grant.get_absolute_url(), ticket.topic.grant),
                "topic": '<a href="%s">%s</a>' % (ticket.topic.get_absolute_url(), ticket.topic),
                "requested_by": ticket.requested_by_html(),
                "requested_expeditures": "%s %s" % (ticket.preexpeditures()['amount'] or 0, settings.TRACKER_CURRENCY),
                "accepted_expeditures": "%s %s" % (ticket.accepted_expeditures(), settings.TRACKER_CURRENCY),
                "paid_expeditures": "%s %s" % (ticket.paid_expeditures(), settings.TRACKER_CURRENCY),
                "state": unicode(ticket.state_str()),
                "changed": unicode(ticket.updated),
            })
        open(os.path.join(settings.STATIC_ROOT, 'tickets.json'), 'w').write(json.dumps(tickets))