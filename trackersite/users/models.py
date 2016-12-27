from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape

class UserWrapper(object):
    def __init__(self, user):
        self.user = user
    
    def __unicode__(self):
        return unicode(self.user)

    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'username':self.user.username})
    
    def get_html_link(self):
        out = '<a href="%s">%s</a>' % (self.get_absolute_url(), escape(unicode(self.user)))
        return mark_safe(out)
