from os import getenv

_user = getenv('USER', getenv('USERNAME', 'default'))
__YOUR_EMAIL__ = '%s@gmail.com' % _user


# configuration
class Config(object):
	app = 'amzn-search-api'
	HEROKU = getenv('HEROKU', False)

	DEBUG = False
	DEBUG_MEMCACHE = True
	ADMINS = frozenset([__YOUR_EMAIL__])
	TESTING = False
	HOST = '127.0.0.1'

	if HEROKU:
		SERVER_NAME = '%s.herokuapp.com' % app

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
