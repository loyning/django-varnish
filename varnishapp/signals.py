from django.db.models.signals import post_save
from django.db.models import get_model
from django.conf import settings
from manager import manager

import logging

logger = logging.getLogger("varnish.invalidation")

def purge_old_paths(abs_url):
    
    """
    If Django redirects app is installed, search for new paths based on given absolute url 
    and purge all the corresponding old paths to ensure the user gets a redirect to the 
    new path and not an old cached version of the page if i.e. the slug has changed.
    """
    
    if "django.contrib.redirects" in settings.INSTALLED_APPS:
        from django.contrib.redirects.models import Redirect
        
        oldpaths = Redirect.objects.filter(new_path=abs_url)
        
        for p in oldpaths:
             
             try:
                 manager.run('purge.url', r'^%s$' % str(p.old_path))
             except:
                 logger.warn('No varnish instance running. Could not purge %s' % str(p.old_path))

def absolute_url_purge_handler(sender, **kwargs):
    abs_url = kwargs['instance'].get_absolute_url()
    
    try:
        manager.run('purge.url', r'^%s$' % abs_url)
    except:
        logger.warn('No varnish instance running. Could not purge %s ' % abs_url)
    
    purge_old_paths(abs_url)

for model in getattr(settings, 'VARNISH_WATCHED_MODELS', ()):
    post_save.connect(absolute_url_purge_handler, sender=get_model(*model.split('.')))