# -*- coding: utf-8 -*-

""" Interface to Amazon API """

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from os import getenv
from amazon.api import AmazonAPI
from builtins import *  # pylint: disable=F401


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
            one of  ['US', 'UK', 'FR', 'DE', 'IT', 'ES', 'CA', 'JP']

        Keyword Arguments
        -----------------
        see bottlenose docs

        Returns
        -------
        New instance of :class:`Amazon` : Amazon

        Examples
        --------
        >>> Amazon()  # doctest: +ELLIPSIS
        <app.api.Amazon object at 0x...>
        """
        self.region = region
        key = kwargs.pop('key', getenv('AWS_ACCESS_KEY_ID'))
        secret = kwargs.pop('secret', getenv('AWS_SECRET_ACCESS_KEY'))
        tag = kwargs.pop('tag', getenv('AWS_ASSOCIATE_TAG_%s' % region, 'na'))

        if not (key and secret and tag):
            raise SystemExit('Error getting Amazon credentials.')

        super(Amazon, self).__init__(key, secret, tag, region)

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
        >>> amazon = Amazon(region='UK')
        >>> kwargs = {
        ...     'SearchIndex': 'All', 'Keywords': 'Harry Potter',
        ...     'ResponseGroup': 'Medium'}
        >>> amzn_response = amazon.search_n(1, **kwargs)
        >>> parsed = list(amazon.parse(amzn_response))
        >>> sorted(parsed[0].keys()) == [
        ...     'asin', 'country', 'currency', 'model', 'price', 'sales_rank',
        ...     'title', 'url']
        True
        >>> url = parsed[0]['url']
        >>> '.'.join(url.split('/')[2].split('.')[2:]) == 'co.uk'
        True
        """
        for r in response:
            yield {
                'asin': r.asin,
                'model': r.model,
                'url': r.offer_url,
                'title': r.title,
                'price': (r.price_and_currency[0] or 0),
                'country': self.region,
                'currency': r.price_and_currency[1],
                'sales_rank': r._safe_get_element_text('SalesRank'),
            }
