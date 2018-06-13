"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for interfacing with the Jama REST API

The API is documented by the following resources:
https://dev.jamasoftware.com/rest
http://jama03.rockwellcollins.com/contour/rest/latest/api-docs/
"""
import copy
import datetime
import pytz
from collections import OrderedDict

from dictutils import dict_update
from rest_api import RestApi, HttpException


__version__ = '$Rev: 250737 $'


class JamaHttpException(HttpException):
    """Exception raised to indicate an unsuccessful HTTP request to Jama"""
    def __init__(self, method, response):
        """
        Constructor called in instantiation.  Creates an exception which 
        indicates an unsuccessful HTTP request the Jama API.

        :param method: HTTP method used in the request
        :type  method: RestHttpMethod
        :param response: response given for the request
        :type  response: requests.Response
        """
        message = None
        try:
            data = response.json()

        except ValueError:
            pass

        else:
            if 'meta' in data:
                message = '{status} - {msg}'.format(
                    status=data['meta'].get('status'),
                    msg=data['meta'].get('message'))

        HttpException.__init__(self, method, response, message=message)


class InvalidResponseException(Exception):
    """Exception raised when a response is invalid"""
    def __init__(self, response):
        """
        Constructor called in instantiation.  Creates an exception which
        indicates an invalid response.

        :param response: response given for the request
        :type  response: requests.Response
        """
        self.response = response
        Exception.__init__(
            self, 'Response for "{url}" was invalid:\n{content}'.format(
                url=response.url,
                content=response.content))


class JamaRestApi(RestApi):
    """Interface for the Jama HTTP REST API"""

    # base URL for the Jama REST API
    BASE = 'http://{server}.rockwellcollins.com/contour/rest/latest/'

    # headers for the Jama REST API
    HEADERS = {
        'Content-Type': 'application/json'
    }

    # default number of resources to get per request
    DEFAULT_BATCH_SIZE = 50

    # rate limiter
    ASYNC_REQ_BATCH_SIZE = 10
    MIN_REQUEST_DELAY = datetime.timedelta(microseconds=500000)

    def __init__(self, auth=None, server='jama03'):
        """
        Constructor called in instantiation.  Creates a client for issuing REST 
        API calls to Jama.

        :param auth: username and password to authenticate with Jama
        :type  auth: tuple(basestring, basestring)
        """
        self.BASE = self.BASE.format(server=server)
        RestApi.__init__(
            self,
            auth_dialog_title='Jama Auth',
            auth_dialog_message=(
                'Please provide your credentials to\n'
                'access the Jama API'),
            auth=auth)

    def _bad_response(self, method, response):
        """
        Handles a "bad" response (when the status code is not 2XX).

        :param method: HTTP method used to the request
        :type  method: RestHttpMethod
        :param response: response given for the request
        :type  response: requests.Response
        """
        raise JamaHttpException(method, response)

    @staticmethod
    def _date_str(date):
        """
        Converts a date to an ISO 8601 string with a UTC offset.

        :param date: datetime to convert
        :type  date: datetime.datetime
        :return: ISO 8601 representation of the date
        :rtype: basestring
        """
        if date.tzinfo is None:
            date = pytz.utc.localize(date)

        return date.isoformat()

    def get_all(self, path, query=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all resources from a collection.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param path: path to the resource
        :type  path: basestring
        :param query: arguments used to query the resource
        :type  query: dict
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all resources from the collection
        :rtype: list[dict]
        """
        if query is None:
            query = {}

        # get total items
        req_query = copy.deepcopy(query)
        req_query.update({'maxResults': 1})
        data = self.get(path, query=req_query).json()
        total_items = data['meta']['pageInfo']['totalResults']

        # create URLs
        urls = OrderedDict()
        for index in xrange(0, total_items, batch_size):
            req_query = copy.deepcopy(query)
            req_query.update({
                'maxResults': batch_size,
                'startAt': index
            })

            urls[self.url(path, query=req_query)] = (index, 0, path, req_query)

        # execute requests
        valid_responses = {}
        for _ in xrange(6):
            if len(urls) == 0:
                break

            responses = self.get_async(urls.keys())

            # retry invalid responses
            new_urls = OrderedDict()
            for response in responses:
                index, subindex, path, req_query = urls[response.url]
                if response.content:
                    # valid response
                    if index not in valid_responses:
                        valid_responses[index] = {}

                    valid_responses[index][subindex] = response
                    continue

                # Jama server request timed out
                for i in xrange(req_query['maxResults']):
                    start = req_query['startAt'] + i
                    if start >= total_items:
                        break

                    if req_query['maxResults'] > 1:
                        subindex = i

                    new_query = {
                        'maxResults': 1,
                        'startAt': start,
                    }

                    new_urls[self.url(path, query=new_query)] = (
                        index, subindex, path, new_query)

            urls = new_urls

        # collect data from responses
        out = []
        for index in sorted(valid_responses.keys()):
            for subindex in sorted(valid_responses[index].keys()):
                response = valid_responses[index][subindex]
                out.extend(response.json().get('data', []))

        return out

    # abstract items
    def get_abstract_items(
            self, project_id=None, item_type_id=None, document_key=None,
            release_id=None, created_after=None, modified_after=None,
            last_activity_after=None, contains=None, sort_by=None,
            start_at=None, max_results=None):
        """
        Searches Jama for items, test plans, test cycles, test runs, or 
        attachments which match the criteria.

        :param project_id: Jama project ID which contains the items
        :type  project_id: int
        :param item_type_id: Jama item type ID used by the items
        :type  item_type_id: int
        :param document_key: Jama document key used by the items
                             (eg. COL-SysReq-1234)
        :type  document_key: basestring
        :param release_id: Jama release ID which contains the items
        :type  release_id: int
        :param created_after: filter by created after a date and time
        :type  created_after: datetime.datetime
        :param modified_after: filter by modified after a date and time
        :type  modified_after: datetime.datetime
        :param last_activity_after: filter by activity after a date and time
        :type  last_activity_after: datetime.datetime
        :param contains: filter on the text contents of the item
        :type  contains: basestring or list[basestring]
        :param sort_by: name of the field by which to sort, followed by ".asc" 
                        or ".desc" (defaults to "sequence.asc")
        :type  sort_by: basestring or list[basestring]
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama search results
        :rtype: dict
        """
        query = {}
        if project_id is not None:
            query['project'] = project_id

        if item_type_id is not None:
            query['itemType'] = item_type_id

        if document_key is not None:
            query['documentKey'] = document_key

        if release_id is not None:
            query['release'] = release_id

        if created_after is not None:
            query['createdDate'] = self._date_str(created_after)

        if modified_after is not None:
            query['modifiedDate'] = self._date_str(modified_after)

        if last_activity_after is not None:
            query['lastActivityDate'] = self._date_str(last_activity_after)

        if contains is not None:
            if isinstance(contains, list):
                contains = ';'.join(contains)

            query['contains'] = contains

        if sort_by is not None:
            if isinstance(sort_by, list):
                sort_by = ';'.join(sort_by)

            query['sortBy'] = sort_by

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('abstractitems', query=query).json()

    def search(self, *args, **kwargs):
        """
        Searches Jama for all items, test plans, test cycles, test runs, or 
        attachments which match the criteria (same as get_abstract_items).
        """
        return self.get_abstract_items(*args, **kwargs)

    def get_all_abstract_items(
            self, project_id=None, item_type_id=None, document_key=None,
            release_id=None, created_after=None, modified_after=None,
            last_activity_after=None, contains=None, sort_by=None,
            batch_size=DEFAULT_BATCH_SIZE):
        """
        Searches Jama for all items, test plans, test cycles, test runs, or 
        attachments which match the criteria.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID which contains the items
        :type  project_id: int
        :param item_type_id: Jama item type ID used by the items
        :type  item_type_id: int
        :param document_key: Jama document key used by the items
                             (eg. COL-SysReq-1234)
        :type  document_key: basestring
        :param release_id: Jama release ID which contains the items
        :type  release_id: int
        :param created_after: filter by created after a date and time
        :type  created_after: datetime.datetime
        :param modified_after: filter by modified after a date and time
        :type  modified_after: datetime.datetime
        :param last_activity_after: filter by activity after a date and time
        :type  last_activity_after: datetime.datetime
        :param contains: filter on the text contents of the item
        :type  contains: basestring or list[basestring]
        :param sort_by: name of the field by which to sort, followed by ".asc" 
                        or ".desc" (defaults to "sequence.asc")
        :type  sort_by: basestring or list[basestring]
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama search results
        :rtype: dict
        """
        query = {}
        if project_id is not None:
            query['project'] = project_id

        if item_type_id is not None:
            query['itemType'] = item_type_id

        if document_key is not None:
            query['documentKey'] = document_key

        if release_id is not None:
            query['release'] = release_id

        if created_after is not None:
            query['createdDate'] = self._date_str(created_after)

        if modified_after is not None:
            query['modifiedDate'] = self._date_str(modified_after)

        if last_activity_after is not None:
            query['lastActivityDate'] = self._date_str(last_activity_after)

        if contains is not None:
            if isinstance(contains, list):
                contains = ';'.join(contains)

            query['contains'] = contains

        if sort_by is not None:
            if isinstance(sort_by, list):
                sort_by = ';'.join(sort_by)

            query['sortBy'] = sort_by

        return self.get_all('abstractitems', query=query, batch_size=batch_size)

    def complete_search(self, *args, **kwargs):
        """
        Searches Jama for all items, test plans, test cycles, test runs, or 
        attachments which match the criteria (same as get_all_abstract_items).

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.
        """
        return self.get_all_abstract_items(*args, **kwargs)

    def get_abstract_item(self, item_id):
        """
        Gets a Jama item, test plan, test cycle, test run, or attachment.

        :param item_id: Jama item ID
        :type  item_id: int
        :return: response containing the Jama item
        :rtype: dict
        """
        return self.get('abstractitems/{}'.format(item_id)).json()

    # baselines
    def get_baselines(self, project_id, start_at=None, max_results=None):
        """
        Gets Jama baselines in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama baselines in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('baselines', query=query).json()

    def get_all_baselines(self, project_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama baselines in a project.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama baselines in the project
        :rtype: list[dict]
        """
        query = {'project': project_id}
        return self.get_all('baselines', query=query, batch_size=batch_size)

    def get_baseline(self, baseline_id):
        """
        Gets a Jama item.

        :param baseline_id: Jama baseline ID
        :type  baseline_id: int
        :return: response containing the Jama baseline
        :rtype: dict
        """
        return self.get('baselines/{}'.format(baseline_id)).json()

    # comments
    def get_comments(
            self, item_id=None, root_comments_only=None, start_at=None,
            max_results=None):
        """
        Gets Jama comments.

        :param item_id: filter by Jama item ID
        :type  item_id: int
        :param root_comments_only: only get root comments without replies
        :type  root_comments_only: bool
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama comments
        :rtype: dict
        """
        if item_id is not None:
            path = 'items/{}/comments'.format(item_id)

        else:
            path = 'comments'

        query = {}
        if root_comments_only is not None:
            query['rootCommentsOnly'] = root_comments_only

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(path, query=query).json()

    def get_all_comments(
            self, item_id=None, root_comments_only=None,
            batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama comments.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: filter by Jama item ID
        :type  item_id: int
        :param root_comments_only: only get root comments without replies
        :type  root_comments_only: bool
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama comments
        :rtype: list[dict]
        """
        if item_id is not None:
            path = 'items/{}/comments'.format(item_id)

        else:
            path = 'comments'

        query = {}
        if root_comments_only is not None:
            query['rootCommentsOnly'] = root_comments_only

        return self.get_all(path, query=query, batch_size=batch_size)

    def create_comment(
            self, created_by, status, text, reply_to=None, item_id=None,
            **data):
        """
        Creates a new Jama comment.

        :param created_by: Jama user ID for the comment author
        :type  created_by: int
        :param status: Jama comment status
        :type  status: basestring
        :param text: Jama comment body (expressed as HTML)
        :type  text: basestring
        :param reply_to: Jama comment ID being replied to
        :type  reply_to: int
        :param item_id: Jama item ID for the comment to be attached to
        :type  item_id: int
        :return: response data
        :rtype: dict
        """
        payload = {
            'createdBy': created_by,
            'status': status,
            'body': {'text': text}
        }

        if reply_to is not None:
            payload['inReplyTo'] = reply_to

        if item_id is not None:
            payload['location'] = {'item': item_id}

        payload = dict_update(payload, data)
        return self.post('comments', payload=payload).json()

    def get_comment(self, comment_id):
        """
        Gets a Jama comment.

        :param comment_id: Jama comment ID
        :type  comment_id: int
        :return: response containing the Jama comment
        :rtype: dict
        """
        return self.get('comments/{}'.format(comment_id)).json()

    # comment replies
    def get_replies(self, comment_id, start_at=None, max_results=None):
        """
        Gets replies to a Jama comment.

        :param comment_id: Jama comment ID of the root comment
        :type  comment_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing replies to the comment
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'comments/{}/replies'.format(comment_id),
            query=query).json()

    def get_all_replies(self, comment_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all replies to a Jama comments.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param comment_id: Jama comment ID of the root comment
        :type  comment_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all replies to the comment
        :rtype: list[dict]
        """
        return self.get_all(
            'comments/{}/replies'.format(comment_id),
            batch_size=batch_size)

    # filters
    def get_filters(
            self, project_id, author_id=None, start_at=None, max_results=None):
        """
        Gets Jama filters in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param author_id: Jama user ID of the author
        :type  author_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama filters in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if author_id is not None:
            query['author'] = author_id

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('filters', query=query).json()

    def get_all_filters(
            self, project_id, author_id=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama filters.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param author_id: Jama user ID of the author
        :type  author_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama filters in the project
        :rtype: list[dict]
        """
        query = {'project': project_id}
        if author_id is not None:
            query['author'] = author_id

        return self.get_all('filters', query=query, batch_size=batch_size)

    def get_filter(self, filter_id):
        """
        Gets a Jama filter.

        :param filter_id: Jama filter ID
        :type  filter_id: int
        :return: response containing the Jama filter
        :rtype: dict
        """
        return self.get('filters/{}'.format(filter_id)).json()

    # filter results
    def get_filter_results(self, filter_id, start_at=None, max_results=None):
        """
        Gets items from a Jama filter.

        :param filter_id: Jama filter ID
        :type  filter_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama baselines in the project
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'filters/{}/results'.format(filter_id),
            query=query).json()

    def get_all_filter_results(self, filter_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all items from a Jama filter.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param filter_id: Jama filter ID
        :type  filter_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama baselines in the project
        :rtype: list[dict]
        """
        return self.get_all(
            'filters/{}/results'.format(filter_id),
            batch_size=batch_size)

    # items
    def get_items(
            self, project_id, root_only=None, start_at=None, max_results=None):
        """
        Gets Jama items in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param root_only: only get root-level nodes from the item tree (defaults 
                          to False)
        :type  root_only: bool
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama items in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if root_only is not None:
            query['rootOnly'] = root_only

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('items', query=query).json()

    def get_all_items(
            self, project_id, root_only=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama items in a project.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param root_only: only get root-level nodes from the item tree (defaults 
                          to False)
        :type  root_only: bool
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama items in the project
        :rtype: list[dict]
        """
        query = {'project': project_id}
        if root_only is not None:
            query['rootOnly'] = root_only

        return self.get_all('items', query=query, batch_size=batch_size)

    def create_item(
            self, project_id, item_type_id, parent_item_id, fields, **data):
        """
        Creates a new Jama item in a project.

        :param project_id: Jama project ID for the new item
        :type  project_id: int
        :param item_type_id: Jama item type ID for the new item
        :type  item_type_id: int
        :param parent_item_id: Jama item ID for the parent item
        :type  parent_item_id: int
        :param fields: field values for the new item
        :type  fields: dict
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'project': project_id,
            'itemType': item_type_id,
            'location': {'parent': {'item': parent_item_id}},
            'fields': fields
        }

        payload = dict_update(payload, data)
        return self.post('items', payload=payload).json()

    def create_folder(
            self, project_id, child_item_type_id, parent_item_id, fields,
            **data):
        """
        Creates a new Jama folder in a project.

        :param project_id: Jama project ID for the new item
        :type  project_id: int
        :param child_item_type_id: Jama item type ID for the child items
        :type  child_item_type_id: int
        :param parent_item_id: Jama item ID for the parent item
        :type  parent_item_id: int
        :param fields: field values fro the new item
        :type  fields: dict
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        return self.create_item(
            project_id=project_id,
            item_type_id=55,
            parent_item_id=parent_item_id,
            fields=fields,
            childItemType=child_item_type_id,
            **data)

    def get_item(self, item_id):
        """
        Gets a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :return: response containing the Jama item
        :rtype: dict
        """
        return self.get('items/{}'.format(item_id)).json()

    def change_item(self, item_id, item_data):
        """
        Changes a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :param item_data: new Jama item data
        :type  item_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put('items/{}'.format(item_id), payload=item_data).json()

    def delete_item(self, item_id):
        """
        Deletes a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        """
        self.delete('items/{}'.format(item_id))

    # item parent
    def get_parent(self, item_id):
        """
        Gets the parent of a Jama item.

        :param item_id: Jama item ID of the child item
        :type  item_id: int
        :return: response containing the parent Jama item
        :rtype: dict
        """
        return self.get('items/{}/parent'.format(item_id)).json()

    # item children
    def get_children(
            self, item_id, start_at=None, max_results=None):
        """
        Gets children of a Jama item.

        :param item_id: Jama item ID of the parent item
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing children of the Jama item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('items/{}/children'.format(item_id), query=query).json()

    def get_all_children(self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all children of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: Jama item ID of the parent item
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all children of the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/children'.format(item_id),
            batch_size=batch_size)

    # synced items
    def get_synced_items(
            self, item_id, start_at=None, max_results=None):
        """
        Gets other items synced with a Jama item.

        :param item_id: Jama item ID of the parent item
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing other items synced with the Jama item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'items/{}/synceditems'.format(item_id),
            query=query).json()

    def get_all_synced_items(self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all other items synced with a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in
        parallel and too many requests can cause the Jama server to become
        unstable.  Some rate limiting is built in, but it should not be relied
        upon.

        :param item_id: Jama item ID of the parent item
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all other items synced with the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/synceditems'.format(item_id),
            batch_size=batch_size)

    # synced items status
    def get_sync_status(
            self, item_id, synced_item_id):
        """
        Gets the sync status between an item and another synced item.

        :param item_id: Jama item ID of the item
        :type  item_id: int
        :param synced_item_id: Jama item ID of the synced item
        :type  synced_item_id: int
        :return: response containing the sync status
        :rtype: dict
        """
        return self.get(
            'items/{item}/synceditems/{synced_item}/syncstatus'.format(
                item=item_id,
                synced_item=synced_item_id)).json()

    # item location
    def get_location(self, item_id):
        """
        Gets the location of a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :return: response containing Jama item location
        :rtype: dict
        """
        return self.get('items/{}/location'.format(item_id)).json()

    def change_location(self, item_id, item_location_data):
        """
        Changes the location of a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :param item_location_data: new Jama item location data
        :type  item_location_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'items/{}/location'.format(item_id),
            payload=item_location_data).json()

    # item upstream relationships
    def get_upstream_relationships(
            self, item_id, start_at=None, max_results=None):
        """
        Gets upstream relationships of a Jama item.

        :param item_id: Jama item ID of the downstream item
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing upstream relationships of the Jama item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'items/{}/upstreamrelationships'.format(item_id),
            query=query).json()

    def get_all_upstream_relationships(
            self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all upstream relationships of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: Jama item ID of the downstream item
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all upstream relationships of the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/upstreamrelationships'.format(item_id),
            batch_size=batch_size)

    def get_all_upstream_items(self, item_id):
        """
        Gets all upstream items of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        WARNING: In order to get the item data, this API makes a separate 
        Jama request for EACH relationship.  Use extra caution and avoid using
        this on items with many relationships.

        :param item_id: Jama item ID of the downstream item
        :type  item_id: int
        :return: all upstream items of the Jama item
        :rtype: list[dict]
        """
        relationships = self.get_all_upstream_relationships(item_id)
        responses = self.get_async([
            self.url('items/{}'.format(r['fromItem']))
            for r in relationships])

        return [r.json()['data'] for r in responses]

    # item downstream relationships
    def get_downstream_relationships(
            self, item_id, start_at=None, max_results=None):
        """
        Gets downstream relationships of a Jama item.

        :param item_id: Jama item ID of the upstream item
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing downstream relationships of the Jama item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'items/{}/downstreamrelationships'.format(item_id),
            query=query).json()

    def get_all_downstream_relationships(
            self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all downstream relationships of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: Jama item ID of the upstream item
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all downstream relationships of the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/downstreamrelationships'.format(item_id),
            batch_size=batch_size)

    def get_all_downstream_items(self, item_id):
        """
        Gets all downstream items of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        WARNING: In order to get the item data, this API makes a separate 
        Jama request for EACH relationship.  Use extra caution and avoid using
        this on items with many relationships.

        :param item_id: Jama item ID of the upstream item
        :type  item_id: int
        :return: all downstream items of the Jama item
        :rtype: list[dict]
        """
        relationships = self.get_all_downstream_relationships(item_id)
        responses = self.get_async([
            self.url('items/{}'.format(r['toItem']))
            for r in relationships])

        return [r.json()['data'] for r in responses]

    # item versions
    def get_versions(self, item_id, start_at=None, max_results=None):
        """
        Gets versions of a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing versions of the Jama item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'items/{}/versions'.format(item_id),
            query=query).json()

    def get_all_versions(self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all versions of a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: Jama item ID
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all versions of the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/versions'.format(item_id),
            batch_size=batch_size)

    # item workflow transitions
    def transition_item(self, item_id, transition_id):
        """
        Executes a workflow transition an item.  Valid transitions can be found
        by calling get_all_workflow_transition_options().

        :param item_id: Jama item ID
        :type  item_id: int
        :param transition_id: Jama transition ID for the new item workflow state
        :type  transition_id: int
        :return: response data
        :rtype: dict
        """
        payload = {'transitionId': transition_id}
        return self.post(
            'items/{}/workflowtransitions'.format(item_id),
            payload=payload).json()

    # item workflow transition options
    def get_workflow_transition_options(
            self, item_id, start_at=None, max_results=None):
        """
        Gets workflow transition options for a Jama item.

        :param item_id: Jama item ID
        :type  item_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing workflow transition options for the Jama
                 item
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'items/{}/workflowtransitionoptions'.format(item_id),
            query=query).json()

    def get_all_workflow_transition_options(
            self, item_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all workflow transition options for a Jama item.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param item_id: Jama item ID
        :type  item_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all workflow transition options for the Jama item
        :rtype: list[dict]
        """
        return self.get_all(
            'items/{}/workflowtransitionoptions'.format(item_id),
            batch_size=batch_size)

    # item types
    def get_item_types(self, project_id=None, start_at=None, max_results=None):
        """
        Gets Jama item types.

        :param project_id: filter by Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama item types
        :rtype: dict
        """
        if project_id is not None:
            path = 'projects/{}/itemtypes'.format(project_id)

        else:
            path = 'itemtypes'

        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(path, query=query).json()

    def get_all_item_types(
            self, project_id=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama item types.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: filter by Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all downstream relationships of the Jama item
        :rtype: list[dict]
        """
        if project_id is not None:
            path = 'projects/{}/itemtypes'.format(project_id)

        else:
            path = 'itemtypes'

        return self.get_all(path, batch_size=batch_size)

    def get_item_type(self, item_type_id):
        """
        Gets a Jama item type.

        :param item_type_id: Jama item type ID
        :type  item_type_id: int
        :return: response containing the Jama item type
        :rtype: dict
        """
        return self.get('itemtypes/{}'.format(item_type_id)).json()

    # pick lists
    def get_pick_lists(self, start_at=None, max_results=None):
        """
        Gets Jama pick lists.

        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama pick lists
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('picklists', query=query).json()

    def get_all_pick_lists(self, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama pick lists.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama pick lists
        :rtype: list[dict]
        """
        return self.get_all('picklists', batch_size=batch_size)

    def get_pick_list(self, pick_list_id):
        """
        Gets a Jama pick list.

        :param pick_list_id: Jama pick list ID
        :type  pick_list_id: int
        :return: response containing the Jama pick list
        :rtype: dict
        """
        return self.get('picklists/{}'.format(pick_list_id)).json()

    # pick list options
    def get_pick_list_options(
            self, pick_list_id, start_at=None, max_results=None):
        """
        Gets options for a Jama pick list.

        :param pick_list_id: Jama pick list ID
        :type  pick_list_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing options for a Jama pick list
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'picklists/{}/options'.format(pick_list_id),
            query=query).json()

    def get_all_pick_list_options(
            self, pick_list_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all options for a Jama pick list.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param pick_list_id: Jama pick list ID
        :type  pick_list_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all options for a Jama pick list
        :rtype: list[dict]
        """
        return self.get_all(
            'picklists/{}/options'.format(pick_list_id),
            batch_size=batch_size)

    # projects
    def get_projects(self, start_at=None, max_results=None):
        """
        Gets Jama projects.

        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama projects in the project
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('items', query=query).json()

    def get_all_projects(self, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama projects.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama projects
        :rtype: list[dict]
        """
        return self.get_all('projects', batch_size=batch_size)

    def create_project(
            self, name, description, project_key, project_folder_id, **data):
        """
        Creates a new Jama project.

        :param name: name of the project
        :type  name: basestring
        :param description: short description of the project
        :type  description: basestring
        :param project_key: character sequence used to identify items
        :type  project_key: basestring
        :param project_folder_id: Jama project ID for the folder to create the 
                                  new project in
        :type  project_folder_id: int
        :return: response data
        :rtype: dict
        """
        payload = {
            'projectKey': project_key,
            'parent': project_folder_id,
            'isFolder': False,
            'fields': {
                'name': name,
                'description': description
            }
        }

        payload = dict_update(payload, data)
        return self.post('projects', payload=payload).json()

    def create_project_folder(
            self, name, description, project_folder_id, **data):
        """
        Creates a new Jama project folder.

        :param name: name of the project
        :type  name: basestring
        :param description: short description of the project
        :type  description: basestring
        :param project_folder_id: Jama project ID for the folder to create the 
                                  new project folder in
        :type  project_folder_id: int
        :return: response data
        :rtype: dict
        """
        payload = {
            'parent': project_folder_id,
            'isFolder': True,
            'fields': {
                'name': name,
                'description': description
            }
        }

        payload = dict_update(payload, data)
        return self.post('projects', payload=payload).json()

    def get_project(self, project_id):
        """
        Gets a Jama project.

        :param project_id: Jama project ID
        :type  project_id: int
        :return: response containing the Jama project
        :rtype: dict
        """
        return self.get('projects/{}'.format(project_id)).json()

    def change_project(self, project_id, project_data):
        """
        Changes a Jama project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param project_data: new Jama project data
        :type  project_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'projects/{}'.format(project_id),
            payload=project_data).json()

    # relationships
    def get_relationships(self, project_id, start_at=None, max_results=None):
        """
        Gets Jama item relationships in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama item relationships in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('relationships', query=query).json()

    def get_all_relationships(self, project_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama item relationships in a project.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama item relationships in the project
        :rtype: list[dict]
        """
        return self.get_all(
            'relationships',
            query={'project': project_id},
            batch_size=batch_size)

    def create_relationship(
            self, from_item_id, to_item_id, relationship_type_id, **data):
        """
        Creates a relationship between two Jama items.

        :param from_item_id: Jama item ID for the source item
        :type  from_item_id: int
        :param to_item_id: Jama item type ID for the target item
        :type  to_item_id: int
        :param relationship_type_id: Jama item relationship type ID for the new 
                                     relationship
        :type  relationship_type_id: int
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'fromItem': from_item_id,
            'toItem': to_item_id,
            'relationshipType': relationship_type_id
        }

        payload = dict_update(payload, data)
        return self.post('relationships', payload=payload).json()

    def get_relationship(self, relationship_id):
        """
        Gets a Jama item relationship.

        :param relationship_id: Jama item relationship ID
        :type  relationship_id: int
        :return: response containing the Jama item relationship
        :rtype: dict
        """
        return self.get('relationships/{}'.format(relationship_id)).json()

    def change_relationship(self, relationship_id, relationship_data):
        """
        Changes a Jama item relationship.

        :param relationship_id: Jama item relationship ID
        :type  relationship_id: int
        :param relationship_data: new Jama item relationship data
        :type  relationship_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'relationships/{}'.format(relationship_id),
            payload=relationship_data).json()

    def delete_relationship(self, relationship_id):
        """
        Deletes a Jama item relationship.

        :param relationship_id: Jama item relationship ID
        :type  relationship_id: int
        """
        self.delete('relationships/{}'.format(relationship_id))

    # relationship types
    def get_relationship_types(self, start_at=None, max_results=None):
        """
        Gets Jama item relationship types.

        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama relationship types
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('relationshiptypes', query=query).json()

    def get_all_relationship_types(self, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama item relationship types.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama item relationship types
        :rtype: list[dict]
        """
        return self.get_all('relationshiptypes', batch_size=batch_size)

    def get_relationship_type(self, relationship_type_id, timestamp=None):
        """
        Gets a Jama item relationship type.

        :param relationship_type_id: Jama item relationship type ID
        :type  relationship_type_id: int
        :param timestamp: get relationship type at this date and time
        :type  timestamp: datetime.datetime
        :return: response containing the Jama item relationship type
        :rtype: dict
        """
        query = {}
        if timestamp is not None:
            query['timestamp'] = self._date_str(timestamp)

        return self.get(
            'relationshiptypes/{}'.format(relationship_type_id),
            query=query).json()

    # releases
    def get_releases(self, project_id, start_at=None, max_results=None):
        """
        Gets Jama releases in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama releases in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('releases', query=query).json()

    def get_all_releases(self, project_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama releases in a project.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama releases in the project
        :rtype: list[dict]
        """
        query = {'project': project_id}
        return self.get_all('releases', query=query, batch_size=batch_size)

    def create_release(
            self, project_id, name, description, **data):
        """
        Creates a new Jama release in a project.

        :param project_id: Jama project ID for the new release
        :type  project_id: int
        :param name: name of the release
        :type  name: basestring
        :param description: short description of the release
        :type  description: basestring
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'project': project_id,
            'name': name,
            'description': description
        }

        payload = dict_update(payload, data)
        return self.post('releases', payload=payload).json()

    def get_release(self, release_id):
        """
        Gets a Jama release.

        :param release_id: Jama release ID
        :type  release_id: int
        :return: response containing the Jama release
        :rtype: dict
        """
        return self.get('releases/{}'.format(release_id)).json()

    def change_release(self, release_id, release_data):
        """
        Changes a Jama release.

        :param release_id: Jama release ID
        :type  release_id: int
        :param release_data: new Jama release data
        :type  release_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'releases/{}'.format(release_id),
            payload=release_data).json()

    # tags
    def get_tags(self, project_id, start_at=None, max_results=None):
        """
        Gets Jama tags in a project.

        :param project_id: Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama tags in the project
        :rtype: dict
        """
        query = {'project': project_id}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('tags', query=query).json()

    def get_all_tags(self, project_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama tags in a project.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama tags in the project
        :rtype: list[dict]
        """
        query = {'project': project_id}
        return self.get_all('tags', query=query, batch_size=batch_size)

    def create_tag(self, project_id, name, **data):
        """
        Creates a new Jama tag in a project.

        :param project_id: Jama project ID for the new tag
        :type  project_id: int
        :param name: name of the tag
        :type  name: basestring
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'project': project_id,
            'name': name,
        }

        payload = dict_update(payload, data)
        return self.post('tags', payload=payload).json()

    def get_tag(self, tag_id):
        """
        Gets a Jama tag.

        :param tag_id: Jama tag ID
        :type  tag_id: int
        :return: response containing the Jama tag
        :rtype: dict
        """
        return self.get('tags/{}'.format(tag_id)).json()

    def change_tag(self, tag_id, tag_data):
        """
        Changes a Jama tag.

        :param tag_id: Jama user ID
        :type  tag_id: int
        :param tag_data: new Jama tag data
        :type  tag_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'tags/{}'.format(tag_id),
            payload=tag_data).json()

    def delete_tag(self, tag_id):
        """
        Deletes a Jama tag.

        :param tag_id: Jama tag ID
        :type  tag_id: int
        """
        self.delete('tags/{}'.format(tag_id))

    # tag items
    def get_tag_items(self, tag_id, start_at=None, max_results=None):
        """
        Gets items from a Jama tag.

        :param tag_id: Jama tag ID
        :type  tag_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing items from a Jama tag
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'tag/{}/items'.format(tag_id),
            query=query).json()

    def get_all_tag_items(self, tag_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all items from a Jama tag.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param tag_id: Jama tag ID
        :type  tag_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all items from a Jama tag
        :rtype: list[dict]
        """
        return self.get_all(
            'tags/{}/items'.format(tag_id),
            batch_size=batch_size)

    # users
    def get_users(
            self, username=None, email=None, first_name=None, last_name=None,
            include_inactive=None, start_at=None, max_results=None):
        """
        Gets Jama users.

        :param username: filter by Jama username
        :type  username: basestring
        :param email: filter by email address
        :type  email: basestring
        :param first_name: filter by first name
        :type  first_name: basestring
        :param last_name: filter by last name
        :type  last_name: basestring
        :param include_inactive: whether to include inactive users
        :type  include_inactive: bool
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama users
        :rtype: dict
        """
        query = {}
        if username is not None:
            query['username'] = username

        if email is not None:
            query['email'] = email

        if first_name is not None:
            query['firstName'] = first_name

        if last_name is not None:
            query['firstName'] = last_name

        if include_inactive is not None:
            query['includeInactive'] = include_inactive

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('users', query=query).json()

    def get_all_users(
            self, username=None, email=None, first_name=None, last_name=None,
            include_inactive=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama users.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param username: filter by Jama username
        :type  username: basestring
        :param email: filter by email address
        :type  email: basestring
        :param first_name: filter by first name
        :type  first_name: basestring
        :param last_name: filter by last name
        :type  last_name: basestring
        :param include_inactive: whether to include inactive users
        :type  include_inactive: bool
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama users
        :rtype: list[dict]
        """
        query = {}
        if username is not None:
            query['username'] = username

        if email is not None:
            query['email'] = email

        if first_name is not None:
            query['firstName'] = first_name

        if last_name is not None:
            query['firstName'] = last_name

        if include_inactive is not None:
            query['includeInactive'] = include_inactive

        return self.get_all('users', query=query, batch_size=batch_size)

    def create_user(self, username, email, first_name, last_name, **data):
        """
        Creates a new Jama user.

        :param username: Jama username of the new user
        :type  username: basestring
        :param email: email address of the new user
        :type  email: basestring
        :param first_name: first name of the new user
        :type  first_name: basestring
        :param last_name: last name of the new user
        :type  last_name: basestring
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'username': username,
            'email': email,
            'firstName': first_name,
            'lastName': last_name
        }

        payload = dict_update(payload, data)
        return self.post('users', payload=payload).json()

    def get_user(self, user_id):
        """
        Gets a Jama user.

        :param user_id: Jama user ID
        :type  user_id: int
        :return: response containing the Jama user
        :rtype: dict
        """
        return self.get('users/{}'.format(user_id)).json()

    def get_current_user(self):
        """
        Gets the current Jama user.

        :return: response containing the current Jama user
        :rtype: dict
        """
        return self.get('users/current').json()

    def change_user(self, user_id, user_data):
        """
        Changes a Jama user.

        :param user_id: Jama user ID
        :type  user_id: int
        :param user_data: new Jama user data
        :type  user_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'users/{}'.format(user_id),
            payload=user_data).json()

    # user groups
    def get_user_groups(self, project_id=None, start_at=None, max_results=None):
        """
        Gets Jama user groups.

        :param project_id: filter by Jama project ID
        :type  project_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing Jama user groups
        :rtype: dict
        """
        query = {}
        if project_id is not None:
            query['project'] = project_id

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('usergroups', query=query).json()

    def get_all_user_groups(
            self, project_id=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all Jama user groups.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param project_id: filter by Jama project ID
        :type  project_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all Jama user groups
        :rtype: list[dict]
        """
        query = {}
        if project_id is not None:
            query['project'] = project_id

        return self.get_all('usergroups', query=query, batch_size=batch_size)

    def create_user_group(self, project_id, name, description, **data):
        """
        Creates a new Jama user group in a project.

        :param project_id: Jama project ID for the new user group
        :type  project_id: int
        :param name: name of the user group
        :type  name: basestring
        :param description: short description of the user group
        :type  description: basestring
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response data
        :rtype: dict
        """
        payload = {
            'project': project_id,
            'name': name,
            'description': description
        }

        payload = dict_update(payload, data)
        return self.post('usergroups', payload=payload).json()

    def get_user_group(self, user_group_id):
        """
        Gets a Jama user group.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :return: response containing the Jama user group
        :rtype: dict
        """
        return self.get('usergroups/{}'.format(user_group_id)).json()

    def change_user_group(self, user_group_id, user_group_data):
        """
        Changes a Jama user group.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :param user_group_data: new Jama user group data
        :type  user_group_data: dict
        :return: response data
        :rtype: dict
        """
        return self.put(
            'usergroups/{}'.format(user_group_id),
            payload=user_group_data).json()

    def delete_user_group(self, user_group_id):
        """
        Deletes a Jama user group.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        """
        self.delete('usergroups/{}'.format(user_group_id))

    # user group users
    def get_user_group_users(
            self, user_group_id, start_at=None, max_results=None):
        """
        Gets users from a Jama user groups.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 20 and 
                            cannot be larger than 50)
        :type  max_results: int
        :return: response containing users from a Jama user group
        :rtype: dict
        """
        query = {}
        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get(
            'usergroups/{}/users'.format(user_group_id),
            query=query).json()

    def get_all_user_group_users(
            self, user_group_id, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all users from a Jama user group.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all users from a Jama user group
        :rtype: list[dict]
        """
        return self.get_all(
            'usergroups/{}/users'.format(user_group_id),
            batch_size=batch_size)

    def add_user_to_user_group(self, user_id, user_group_id):
        """
        Adds a user to a Jama user group.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :param user_id: Jama user ID
        :type  user_id: int
        :return: response data
        :rtype: dict
        """
        query = {'user': user_id}
        return self.post(
            'usergroups/{}/users'.format(user_group_id),
            query=query).json()

    def remove_user_from_user_group(self, user_id, user_group_id):
        """
        Removes a user from a Jama user group.

        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param user_group_id: Jama user group ID
        :type  user_group_id: int
        :param user_id: Jama user ID
        :type  user_id: int
        """
        return self.delete(
            'usergroups/{user_group_id}/users/{user_id}'.format(
                user_group_id=user_group_id,
                user_id=user_id))
