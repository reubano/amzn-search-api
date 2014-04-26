# -*- coding: utf-8 -*-

""" Interface to Amazon API """
from os import getenv
from amazon.api import AmazonAPI


class Amazon(AmazonAPI):
	"""An Amazon search"""

	def __init__(self, region='US', **kwargs):
		"""
		Initialization method.

		Parameters
		----------
		key : AWS_ACCESS_KEY_ID
		secret : AWS_SECRET_ACCESS_KEY
		tag : AWS_ASSOCIATE_TAG
		region : string
			one of  ['US', 'FR', 'UK', 'CA', 'DE', 'JP', 'IT', 'ES']

		Keyword Arguments
		-----------------
		see bottlenose docs

		Returns
		-------
		New instance of :class:`Amazon` : Amazon

		Examples
		--------
		>>> Amazon()  #doctest: +ELLIPSIS
		<app.api.Amazon object at 0x...>
		"""
		key = kwargs.pop('key', getenv('AWS_ACCESS_KEY_ID'))
		secret = kwargs.pop('secret', getenv('AWS_SECRET_ACCESS_KEY'))
		tag = kwargs.pop('tag', getenv('AWS_ASSOCIATE_TAG'))

		if not (key and secret and tag):
			raise SystemExit('Error getting Amazon credentials.')

		super(Amazon, self).__init__(key, secret, tag, **kwargs)

	def parse(self, response):
		"""
		Convert Amazon API search response into a more readable format.

		Parameters
		----------
		response : AmazonSearch object

		Returns
		-------
		Cleaned up search results : dict

		Examples
		--------
		>>> amazon = Amazon()
		>>> kwargs = {'SearchIndex': 'All', 'Keywords': 'Harry Potter', \
'ResponseGroup': 'Medium'}
		>>> amzn_response = amazon.search_n(1, **kwargs)
		>>> amazon.parse(amzn_response)[0].keys()
		['asin', 'title', 'url', 'price', 'currency', 'sales_rank', 'model']
		"""
		items = []

		for r in response:
			item = {
				'asin': r.asin,
				'model': r.model,
				'url': r.offer_url,
				'title': r.title,
				'price': (r.price_and_currency[0] or 0),
				'currency': r.price_and_currency[1],
				'sales_rank': r._safe_get_element_text('SalesRank'),
			}

			items.append(item)

		return items