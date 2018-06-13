"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for interfacing with an HTTP REST API
"""
import datetime
import threading
import time
try:
    # Python2
    import urlparse
    from urllib import urlencode

except ImportError:
    # Python3
    from urllib import parse as urlparse
    from urllib.parse import urlencode

import grequests
import requests
from enum import Enum

from widgets.auth_dialog import askauth


__version__ = '$Rev: 246449 $'


class RestHttpMethod(Enum):
    """HTTP methods used to invoke REST API calls"""
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class HttpException(Exception):
    """Exception raised to indicate an unsuccessful HTTP request"""
    def __init__(self, method, response, message=None):
        """
        Constructor called in instantiation.  Creates an exception which 
        indicates an unsuccessful HTTP request.
        
        :param method: HTTP method used in the request
        :type  method: RestHttpMethod
        :param response: response given for the request
        :type  response: requests.Response
        :param message: additional text information to describe the issue
        :type  message: basestring
        """
        print method
        msg = '{method} {url} responded with status {status}'.format(
            method=method.value.upper(),
            url=response.url,
            status=response.status_code)

        if message is not None:
            msg = '\n'.join([msg, message])

        Exception.__init__(self, msg)
        self.method = method
        self.response = response


class RestApiAuthException(Exception):
    """Exception raised to indicate an authentication issue"""
    pass


class RestApi(object):
    """Generic interface for an HTTP REST API"""
    _authentication = None
    AUTH_REQUIRED = True

    # mutex to prevent multiple auth requests across threads
    AUTH_LOCK = threading.Lock()

    # base URL for the API
    BASE = None

    # headers for API requests
    HEADERS = None

    # rate limiter
    _request_timer = datetime.datetime(year=1, month=1, day=1)
    MIN_REQUEST_DELAY = datetime.timedelta(microseconds=250000)
    MIN_BATCH_DELAY = datetime.timedelta(seconds=3)
    ASYNC_REQ_LOCK = threading.Lock()
    ASYNC_REQ_BATCH_SIZE = 20

    def __new__(cls, *args, **kwargs):
        """
        Called before instantiation.  Prevents RestApi from being instantiated.
        """
        if cls is RestApi:
            raise TypeError('RestApi may not be instantiated')

        if cls.BASE is None:
            raise TypeError(
                'Class attribute "BASE" must be set to instantiate {}'.format(
                    cls.__name__))

        if cls.HEADERS is None:
            raise TypeError(
                'Class attribute "HEADERS" must be set to instantiate '
                '{}'.format(cls.__name__))

        return object.__new__(cls, *args, **kwargs)

    def __init__(self, auth_dialog_title, auth_dialog_message, auth=None):
        """
        Constructor called in instantiation.  Creates a client for issuing REST 
        API calls.
        
        :param auth_dialog_title: title displayed for the auth dialog
        :type  auth_dialog_title: basestring
        :param auth_dialog_message: message displayed for the auth dialog
        :type  auth_dialog_message: basestring
        :param auth: username and password to authenticate with the API
        :type  auth: tuple(basestring, basestring)
        """
        object.__init__(self)
        self.auth_dialog_title = auth_dialog_title
        self.auth_dialog_message = auth_dialog_message
        self._authentication = auth

    @property
    def _auth(self):
        """
        Provides a username and password to authenticate with the API.  If the
        credentials are not already set on the instance or class, they are
        requested from the user via a dialog box.  If the credentials are not
        set on the class, the credentials provided by the user are set in both
        the instance and the class so that other clients can use them.

        :return: username and password to authenticate with the API
        :rtype: tuple(basestring, basestring)
        """
        self.prompt_for_auth()
        return self._authentication

    def prompt_for_auth(self):
        """
        Make sure a username and password are available to authenticate with the
        API.  If the credentials are not already set on the instance or class,
        they are requested from the user via a dialog box.  If the credentials
        are not set on the class, the credentials provided by the user are set
        in both the instance and the class so that other clients can use them.
        """
        if not self.AUTH_REQUIRED:
            return

        self.__class__.AUTH_LOCK.acquire()
        try:
            if self._authentication is None:
                self._authentication = askauth(
                    self.auth_dialog_title,
                    self.auth_dialog_message)

                if not self._authentication or not all(self._authentication):
                    raise RestApiAuthException(
                        'Missing authentication credentials')

                if self.__class__._authentication is None:
                    self.__class__._authentication = self._authentication

        finally:
            self.__class__.AUTH_LOCK.release()

    def _bad_response(self, method, response):
        """
        Handles a "bad" response (when the status code is not 2XX).
        
        :param method: HTTP method used to the request
        :type  method: RestHttpMethod
        :param response: response given for the request
        :type  response: requests.Response
        """
        raise HttpException(method, response)

    def _rate_limit(self):
        """
        Waits for a reasonable time after the last request.
        """
        while datetime.datetime.now() < self._request_timer:
            time.sleep(0.1)

        self._request_timer = datetime.datetime.now() + self.MIN_REQUEST_DELAY

    def _batch_rate_limit(self):
        """
        Waits for a reasonable time after the last asynchronous batch request.
        """
        while datetime.datetime.now() < self._request_timer:
            time.sleep(0.1)

        self._request_timer = datetime.datetime.now() + self.MIN_BATCH_DELAY

    def url(self, path, query=None):
        """
        Converts a resource path and query to a full URL.

        :param path: the path to the resource
        :type  path: basestring
        :param query: arguments used to query the resource
        :type  query: dict
        :return: the full URL
        :rtype: basestring
        """
        if query is None or len(query) == 0:
            return urlparse.urljoin(self.BASE, path)

        parsed = urlparse.urlsplit(path)
        path = parsed.path
        path_query = urlparse.parse_qs(parsed.query)
        path_query.update(query)
        return urlparse.urljoin(self.BASE, '{path}?{query}'.format(
            path=path,
            query=urlencode(query, doseq=True)))

    def get(self, path, query=None):
        """
        Performs a REST API call to "get" a resource.
        
        :param path: path to the resource
        :type  path: basestring
        :type  query: dict
        :return: REST API response
        :rtype: requests.Response
        """
        self._rate_limit()
        response = requests.get(
            self.url(path, query=query),
            headers=self.HEADERS,
            auth=self._auth)

        if not (200 <= response.status_code < 300):
            self._bad_response(RestHttpMethod.GET, response)

        return response

    def get_async(self, urls, batch_size=None):
        """
        Executes multiple requests asynchronously.  Requests are sent in
        batches every 3 seconds.
        
        :param urls: full URLs to the resource
        :type  urls: list[basestring]
        :param batch_size: number of asynchronous requests to send in each batch
        :type  batch_size: int
        :return: responses from all of the requests
        :rtype: list[requests.Response]
        """
        if batch_size is None:
            batch_size = self.ASYNC_REQ_BATCH_SIZE

        async_requests = [
            grequests.get(
                url,
                headers=self.HEADERS,
                auth=self._auth)
            for url in urls]

        # rate limit requests
        self.ASYNC_REQ_LOCK.acquire()
        try:
            responses = []
            for i in xrange(0, len(async_requests), batch_size):
                self._batch_rate_limit()
                responses.extend(grequests.map(
                    r for r in async_requests[i:i + batch_size]))

            return responses

        finally:
            self.ASYNC_REQ_LOCK.release()

    def post(self, path, query=None, payload=None):
        """
        Performs a REST API call to "post" or "create" a resource.
        
        :param path: path to the resource
        :type  path: basestring
        :param query: arguments used to query the resource
        :type  query: dict
        :param payload: data to create the resource
        :type  payload: dict
        :return: REST API response
        :rtype: requests.Response
        """
        self._rate_limit()
        response = requests.post(
            self.url(path, query=query),
            headers=self.HEADERS,
            json=payload,
            auth=self._auth)

        if not (200 <= response.status_code < 300):
            self._bad_response(RestHttpMethod.POST, response)

        return response

    def put(self, path, query=None, payload=None):
        """
        Performs a REST API call to "put" or "change" a resource.
        
        :param path: path to the resource
        :type  path: basestring
        :param query: arguments used to query the resource
        :type  query: dict
        :param payload: data to update the resource with
        :type  payload: dict
        :return: REST API response
        :rtype: requests.Response
        """
        self._rate_limit()
        response = requests.put(
            self.url(path, query=query),
            headers=self.HEADERS,
            json=payload,
            auth=self._auth)

        if not (200 <= response.status_code < 300):
            self._bad_response(RestHttpMethod.PUT, response)

        return response

    def delete(self, path, query=None):
        """
        Performs a REST API call to "delete" a resource.
        
        :param path: path to the resource
        :type  path: basestring
        :param query: arguments used to query the resource
        :type  query: dict
        :return: REST API response
        :rtype: requests.Response
        """
        self._rate_limit()
        response = requests.delete(
            self.url(path, query=query),
            headers=self.HEADERS,
            auth=self._auth)

        if not (200 <= response.status_code < 300):
            self._bad_response(RestHttpMethod.DELETE, response)

        return response
