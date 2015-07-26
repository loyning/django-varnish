# DJANGO IMPORTS (omji/django-varnish)
try:
    from django.conf.urls import patterns
except ImportError:
    # for Django version less then 1.4
    from django.conf.urls.defaults import patterns


urlpatterns = patterns(
    'varnishapp.views',
    (r'', 'management'),
)
