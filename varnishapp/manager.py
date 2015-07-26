from varnish import VarnishManager
from django.conf import settings
from atexit import register

manager = VarnishManager(getattr(settings, 'VARNISH_MANAGEMENT_ADDRS', ()))
register(manager.close)

from signals import *