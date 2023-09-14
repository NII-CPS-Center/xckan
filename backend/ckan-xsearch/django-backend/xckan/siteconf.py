import json
import os
import ssl

BASEDIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASEDIR, 'logging.json'), 'r') as f:
    BASE_LOGGING_SETTINGS = json.load(f)


class BaseConfig(object):
    # Site environtments
    DEBUG = False  # Production stage
    ADMINS = json.loads(
        os.getenv('ADMINS',
                  '[["root", "root@localhost"]]'))
    SERVER_EMAIL = os.getenv('SERVER_EMAIL',
                             'xckan-notify@localhost')
    SOLR_CKAN_XSEARCH = os.getenv(
        'XCKAN_SOLR',
        'http://localhost:8983/solr/ckan-xsearch/')
    LOGFILE = os.getenv('XCKAN_LOGFILE',
                        os.path.join(BASEDIR, 'logs/xckan.log'))
    CACHEDIR = os.getenv('XCKAN_CACHEDIR',
                         os.path.join(os.getenv('HOME'), 'cache/'))
    LOCKDIR = os.getenv('XCKAN_LOCKDIR', '/tmp/')
    QUERYLOGDIR = os.getenv(
        'XCKAN_QUERYLOGDIR',
        os.path.join(
            os.getenv('HOME'), 'query_log/'))  # Query log
    ACCEPT_SELF_SIGNED = os.getenv('ACCEPT_SELF_SIGNED', False)

    # Django settings
    DJANGO_SETTINGS = {
        'allowed_hosts': os.environ.get(
            'XCKAN_ALLOWED_HOSTS', '.localhost'),
        'databases': {
            'default': {
                'ENGINE': os.environ.get(
                    'XCKAN_DB_ENGINE',
                    'django.db.backends.sqlite3'),
                'NAME': os.environ.get('XCKAN_DB_NAME',
                                       'django-backend/xckan.sqlite3'),
                'USER': os.environ.get('XCKAN_DB_USER', 'xckan'),
                'PASSWORD': os.environ.get(
                    'XCKAN_DB_PASS', 'xckan'),
                'HOST': os.environ.get(
                    'XCKAN_DB_HOST', 'localhost'),
                'PORT': os.environ.get(
                    'XCKAN_DB_PORT', 3306),
                'CONN_MAX_AGE': 600,
            }
        }
    }

    LOGGING_SETTINGS = BASE_LOGGING_SETTINGS
    LOGGING_SETTINGS['handlers']['file']['filename'] = LOGFILE

    def get_ssl_context(self):
        """
        Create an SSL context according to config.
        """
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        if self.__class__.ACCEPT_SELF_SIGNED:
            # Set True if accept self signed certificates
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        return ctx


class DevelopmentConfig(BaseConfig):

    def __init__(self):
        self.DEBUG = True
        self.LOGFILE = os.getenv(
            'XCKAN_LOGFILE',
            os.path.join(BASEDIR, 'logs/xckan_devel.log'))
        self.CACHEDIR = os.getenv(
            'XCKAN_CACHEDIR',
            os.path.join(os.getenv('HOME'), 'cache_devel'))

        self.LOGGING_SETTINGS['handlers']['file']['filename'] = self.LOGFILE
        self.LOGGING_SETTINGS['loggers']['xckan']['level'] = 'DEBUG'
        self.LOGGING_SETTINGS['loggers']['scripts']['level'] = 'DEBUG'


class DevelopmentCloudConfig(DevelopmentConfig):
    # bin/solr start -c -p 8001 -s example/cloud/node1/solr
    # bin/solr start -c -p 8002 -s example/cloud/node2/solr -z localhost:9001

    def __init__(self):
        self.SOLR_CKAN_XSEARCH = (
            'http://localhost:8001/solr/ckan-xsearch/,'
            'http://localhost:8002/solr/ckan-xsearch/')


site_config = BaseConfig()
# site_config = DevelopmentConfig()
# site_config = DevelopmentCloudConfig()
