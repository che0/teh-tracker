import os, sys
from django.template import Template, Context
from django.conf import settings
from django.utils.crypto import get_random_string

MY_PATH = os.path.abspath(os.path.dirname(__file__))

def main():
    target_path = os.path.abspath(os.path.join(MY_PATH, '..', 'trackersite', 'settings.py'))
    if os.path.exists(target_path):
        print 'Don\'t want to overwrite %s.\nIf you\'re sure, delete it and try again.' % target
        sys.exit(1)
    
    # make a template instance
    settings.configure(TEMPLATE_DEBUG=False)
    template_file = open(os.path.join(MY_PATH, 'settings.py.template'))
    template = Template(template_file.read())
    template_file.close()
    
    # set up the options we want
    options = {}
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    options['secret_key'] = get_random_string(50, chars)
        
    context = Context(options)
    target = open(target_path, 'wb')
    target.write(template.render(context))
    target.close()

if __name__ == '__main__':
    main()
