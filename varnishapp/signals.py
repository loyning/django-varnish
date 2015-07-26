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
                 resp = manager.run('ban.url', r'^%s$' % str(p.old_path))
             except:
                 logger.warn('No varnish instance running. Could not purge %s' % str(p.old_path))

def absolute_url_purge_handler(sender, **kwargs):
    """
    Purges the absolute url of the model instance
    NB: It adds $ to the end of the purge, so no urls with parameters etc are purged,
    only the url given by get_absolute_url itself
    """
    instance = kwargs['instance']

    if hasattr(instance, 'get_absolute_url'):
        abs_url = instance.get_absolute_url()

        try:
            banurl = r'^%s$' % abs_url
            logger.info("Banning %s" % banurl)
            resp = manager.run('ban.url', banurl)
            logger.info(resp)
        except:
            logger.warn('No varnish instance running. Could not purge %s ' % abs_url)

        purge_old_paths(abs_url)

for model in getattr(settings, 'VARNISH_WATCHED_MODELS', ()):
    post_save.connect(absolute_url_purge_handler, sender=get_model(*model.split('.')))




def api_resource_purge_handler (sender, **kwargs):

    """
    Purges object urls in the API. Requires a get_resource_url on the model that
    returns the url of the api resource object base url. If using tastypie that would
    look like something like this on a resource named person:

    @models.permalink
    def get_resource_url(self):
           return ('api_dispatch_detail', (), {
                                               'resource_name': 'person',
                                                'api_name': 'v1',
                                                'pk': self.id})

    The method will purge all urls *starting* with the url

    """
    instance = kwargs['instance']

    resource_urls = []
    if hasattr(instance, 'get_resource_url'):
        resource_urls.extend([instance.get_resource_url(), ])

    if hasattr(instance, 'get_related_resource_urls'):
        resource_urls.extend(instance.get_related_resource_urls())

    for resource_url in resource_urls:
        try:
            logger.info('Banning API %s' % resource_url)
            resp = manager.run('ban.url', r'^%s' % resource_url)
            logger.info(resp)
        except:
            logger.warn('No varnish instance running. Could not purge %s ' % resource_url)

        purge_old_paths(resource_url)


for model in getattr(settings, 'VARNISH_WATCHED_MODELS', ()):
    post_save.connect(api_resource_purge_handler, sender=get_model(*model.split('.')))
