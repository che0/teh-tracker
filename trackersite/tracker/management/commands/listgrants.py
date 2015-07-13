from django.core.management.base import NoArgsCommand
from tracker.models import Grant

class Command(NoArgsCommand):
    help = 'List available grants'
    
    def handle_noargs(self, **options):
        for g in Grant.objects.all():
            print g.id, g.short_name, g.full_name
