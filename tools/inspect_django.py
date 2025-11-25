import sys
try:
    import django
    print('DJANGO_FILE:', getattr(django, '__file__', 'NOFILE'))
    import django.core.management as m
    print('HAS_EXECUTE:', hasattr(m, 'execute_from_command_line'))
    import site
    sp = [p for p in sys.path if 'site-packages' in p]
    print('SITE_PACKAGES_PATHS:', sp[-5:])
except Exception as e:
    print('ERROR:', e)
    raise
