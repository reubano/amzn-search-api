from os import getenv, path as p
from slugify import slugify

# module vars
_user = getenv('USER', getenv('USERNAME', 'default'))
_basedir = p.dirname(__file__)

# configurable vars
__APP_NAME__ = 'AMZN Search API'
__YOUR_NAME__ = 'Reuben Cummings'
__YOUR_EMAIL__ = '%s@gmail.com' % _user
__YOUR_WEBSITE__ = 'http://%s.github.com' % _user


# configuration
class Config(object):
    app = slugify(__APP_NAME__)
    stage = getenv('STAGE', False)
    end = '-stage' if stage else ''
    # TODO: programatically get app name
    heroku_server = '%s%s.herokuapp.com' % (app, end)

    APP_NAME = __APP_NAME__
    HEROKU = getenv('HEROKU', False)
    DEBUG = False
    DEBUG_MEMCACHE = True
    ADMINS = frozenset([__YOUR_EMAIL__])
    TESTING = False
    HOST = '127.0.0.1'

    if HEROKU:
        SERVER_NAME = heroku_server

    API_METHODS = ['GET']
    API_MAX_RESULTS_PER_PAGE = 1000
    API_URL_PREFIX = '/api/v1'
    SWAGGER_URL = ''
    SWAGGER_JSON = 'swagger.json'
    SWAGGER_EXCLUDE_COLUMNS = {'utc_created', 'utc_updated'}
    SWAGGER_EXCLUDE_ROUTES = {'static', 'swagger.swagger_json', 'home'}


class Production(Config):
    HOST = '0.0.0.0'


class Development(Config):
    DEBUG = True
    DEBUG_MEMCACHE = False


class Test(Config):
    TESTING = True
    DEBUG_MEMCACHE = False
