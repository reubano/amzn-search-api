from os import getenv
from slugify import slugify

_user = getenv('USER', getenv('USERNAME', 'default'))
__APP_NAME__ = 'AMZN Search API'
__YOUR_EMAIL__ = '%s@gmail.com' % _user


# configuration
class Config(object):
	app = slugify(__APP_NAME__)
	stage = getenv('STAGE', False)
	end = '-stage' if stage else ''
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

	SECRET_KEY = getenv('SECRET_KEY', 'key')
	API_METHODS = ['GET']
	API_MAX_RESULTS_PER_PAGE = 1000
	API_URL_PREFIX = '/api/v1'


class Production(Config):
	HOST = '0.0.0.0'


class Development(Config):
	DEBUG = True
	DEBUG_MEMCACHE = False


class Test(Config):
	TESTING = True
	DEBUG_MEMCACHE = False
