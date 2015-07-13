import os
import zipfile
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from tracker.models import Grant, FinanceStatus

class GrantDumper(object):
    """ This dumps grant into a ZIP file """
    
    def __init__(self, grant, target_filename):
        self.grant = grant
        self.grant_slug = slugify(grant.short_name)
        self.zipname = target_filename
    
    def grant_finance(self):
        topics = []
        grant_finance = FinanceStatus()
        for topic in self.grant.topic_set.all():
            topic_finance = topic.payment_summary()
            grant_finance.add_finance(topic_finance)
            topics.append({'topic':topic, 'finance':topic_finance})
        return {'topics':topics, 'finance':grant_finance}
    
    def dump_index(self):
        """ Dumps index page of the archive """
        index = render_to_string('tracker/dumpaccounts/index.html', {
            'grant': self.grant,
            'date': datetime.datetime.now(),
            'finance': self.grant_finance(),
        }).encode('utf8')
        self.zipfile.writestr('%s/index.html' % self.grant_slug, index)
        self.zipfile.write(finders.find('teh-tracker.css'), '%s/styles.css'  % self.grant_slug)
    
    def dump_ticket(self, ticket):
        index = render_to_string('tracker/dumpaccounts/ticket_detail.html', {
            'grant': self.grant,
            'date': datetime.datetime.now(),
            'ticket': ticket,
        }).encode('utf8')
        self.zipfile.writestr('%s/%s/index.html' % (self.grant_slug, ticket.id), index)
        
        for doc in ticket.document_set.all():
            filepath = doc.payload.path
            zippath = '%s/%s/%s' % (self.grant_slug, ticket.id, doc.filename)
            if os.path.isfile(filepath):
                self.zipfile.write(filepath, zippath)
            else:
                self.zipfile.writestr(zippath + '.MISSING', 'FILE %s MISSING' % doc.filename)
    
    def dump(self):
        """ Do the dumping thing """
        self.zipfile = zipfile.ZipFile(self.zipname, 'w')
        self.dump_index()
        for topic in self.grant.topic_set.all():
            for ticket in topic.ticket_set.all():
                self.dump_ticket(ticket)
        self.zipfile.close()
    

class Command(BaseCommand):
    help = 'Dumps accounts for given grant in a ZIP file'
    
    def dump_accounts(self, **lookup):
        """ Dump accounts for given grant """
        grant = Grant.objects.get(**lookup)
        outfile = slugify(grant.short_name) + '.zip'
        if os.path.exists(outfile):
            raise CommandError('%s already exists' % outfile)
        GrantDumper(grant, outfile).dump()
    
    def handle(self, *args, **options):
        for a in args:
            if a.isdigit():
                self.dump_accounts(id=int(a))
            else:
                self.dump_accounts(short_name=a)
