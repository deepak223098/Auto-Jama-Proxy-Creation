"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for interfacing with the JIRA REST API

The API is documented by the following resources:
https://developer.atlassian.com/jiradev/jira-apis/jira-rest-apis
https://docs.atlassian.com/jira/REST/cloud/
"""
import copy
import pytz

from dictutils import dict_update
from rest_api import RestApi, HttpException


__version__ = '$Rev: 244668 $'


class JiraHttpException(HttpException):
    """Exception raised to indicate an unsuccessful HTTP request to JIRA"""
    def __init__(self, method, response):
        """
        Constructor called in instantiation.  Creates an exception which 
        indicates an unsuccessful HTTP request the JIRA API.
        
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
            if 'errorMessages' in data:
                message = '\n'.join(data['errorMessages'])

            if 'errors' in data:
                if message is None:
                    message = ''

                else:
                    message += '\n'

                message += '\n'.join([
                    '{err} - {msg}'.format(err=err, msg=msg)
                    for err, msg in data['errors'].iteritems()])

        HttpException.__init__(self, method, response, message=message)


class JiraRestApi(RestApi):
    """Interface for the JIRA HTTP REST API"""

    # base URL for the JIRA REST API
    BASE = 'http://alm.rockwellcollins.com/jira/rest/api/2/'

    # headers for the JIRA REST API
    HEADERS = {
        'Content-Type': 'application/json'
    }

    # default number of resources to get per request
    DEFAULT_BATCH_SIZE = 100

    def __init__(self, auth=None):
        """
        Constructor called in instantiation.  Creates a client for issuing REST 
        API calls to JIRA.
        
        :param auth: username and password to authenticate with JIRA
        :type  auth: tuple(basestring, basestring)
        """
        RestApi.__init__(
            self,
            auth_dialog_title='JIRA Auth',
            auth_dialog_message=(
                'Please provide your credentials to\n'
                'access the JIRA API'),
            auth=auth)

    def _bad_response(self, method, response):
        """
        Handles a "bad" response (when the status code is not 2XX).
        
        :param method: HTTP method used to the request
        :type  method: RestHttpMethod
        :param response: response given for the request
        :type  response: requests.Response
        """
        raise JiraHttpException(method, response)

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

    def get_all(
            self, resource, path, query=None, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gets all resources from a collection.
        
        WARNING: Please be careful with this.  The HTTP requests are sent in 
        parallel and too many requests can cause the Jama server to become 
        unstable.  Some rate limiting is built in, but it should not be relied 
        upon.

        :param resource: response field to collect items from
        :type  resource: basestring
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
        total_items = data['total']

        # create URLs
        urls = []
        for index in xrange(0, total_items, batch_size):
            req_query = copy.deepcopy(query)
            req_query.update({
                'maxResults': batch_size,
                'startAt': index
            })

            urls.append(self.url(path, query=req_query))

        # execute requests
        responses = self.get_async(urls)

        out = []
        for response in responses:
            out.extend(response.json().get(resource, []))

        return out

    # issue
    def create_issue(
            self, project_key, issue_type, title, description, reporter=None,
            assignee=None, status=None, labels=None, priority=None,
            due_date=None, update_history=None, **data):
        """
        Creates a new JIRA issue.

        :param project_key: project key to use for the issue (eg. "FMSA")
        :type  project_key: int
        :param issue_type: issue type name (eg. "Work Element")
        :type  issue_type: int
        :param title: summary of the issue
        :type  title: basestring
        :param description: description of the issue
        :type  description: basestring
        :param reporter: username of the user who reported the issue
        :type  reporter: basestring
        :param assignee: username of the user assigned to work on the issue
        :type  assignee: basestring
        :param status: status of the issue (eg. "Open")
        :type  status: basestring
        :param labels: labels used to group the issue with other issues
        :type  labels: list[basestring]
        :param priority: priority of the issue (eg. "(3) Normal Queue")
        :type  priority: basestring
        :param due_date: due date for the issue
        :type  due_date: datetime.datetime
        :param update_history: add the issue to your user issue history
        :type  update_history: bool
        :param data: additional payload values
        :type  data: keyword arguments
        :return: response containing a link to the created issue
        :rtype: dict
        """
        query = {}
        if update_history is not None:
            query['updateHistory'] = update_history

        payload = {
            'fields': {
                'project': {
                    'key': project_key
                },
                'issuetype': {
                    'name': issue_type
                },
                'summary': title,
                'description': description
            }
        }

        if reporter is not None:
            payload['fields']['reporter'] = {'name': reporter}

        if assignee is not None:
            payload['fields']['assignee'] = {'name': assignee}

        if status is not None:
            payload['fields']['status'] = {'name': status}

        if labels is not None:
            payload['fields']['labels'] = labels

        if priority is not None:
            payload['fields']['priority'] = {'name': priority}

        if due_date is not None:
            payload['fields']['duedate'] = self._date_str(due_date)

        payload = dict_update(payload, data)
        return self.post('issue', query=query, payload=payload).json()

    def get_issue(
            self, issue_id, fields=None, expand=None, properties=None,
            fields_by_keys=None, update_history=None):
        """
        Gets a JIRA issue.

        :param issue_id: JIRA issue ID or string
        :type  issue_id: int or basestring
        :param fields: list of fields to return for each issue
        :type  fields: basestring
        :param expand: comma-separated list of the parameters to expand
        :type  expand: basestring
        :param properties: list of properties to return for each issue
        :type  properties: basestring
        :param fields_by_keys: whether to reference fields in issues by keys
                               instead of ids
        :type  fields_by_keys: bool
        :param update_history: add the issue to your user issue history
        :type  update_history: bool
        :return: response containing the JIRA issue
        :rtype: dict
        """
        query = {}
        if fields is not None:
            query['fields'] = fields

        if expand is not None:
            query['expand'] = expand

        if properties is not None:
            query['properties'] = properties

        if fields_by_keys is not None:
            query['fieldsByKeys'] = fields_by_keys

        if update_history is not None:
            query['updateHistory'] = update_history

        return self.get('issue/{}'.format(issue_id), query=query).json()

    def change_issue(
            self, issue_id, issue_data, notify_users=None,
            override_screen_security=None, override_editable_flag=None):
        """
        Changes a JIRA issue.

        :param issue_id: JIRA issue ID or string
        :type  issue_id: int or basestring
        :param issue_data: new JIRA issue data
        :type  issue_data: dict
        :param notify_users: send an email notification to users
        :type  notify_users: bool
        :param override_screen_security: update fields that are not shown on the
                                         screen (requires admin permissions)
        :type  override_screen_security: bool
        :param override_editable_flag: update the issue even if the editable
                                       flag is set to False (requires admin
                                       permissions)
        :type  override_editable_flag: bool
        """
        query = {}
        if notify_users is not None:
            query['notifyUsers'] = notify_users

        if override_screen_security is not None:
            query['overrideScreenSecurity'] = override_screen_security

        if override_editable_flag is not None:
            query['overrideEditableFlag'] = override_editable_flag

        self.put('issue/{}'.format(issue_id), query=query, payload=issue_data)

    def delete_issue(self, issue_id, delete_subtasks=None):
        """
        Deletes a JIRA issue.

        :param issue_id: JIRA issue ID or string
        :type  issue_id: int or basestring
        :param delete_subtasks: whether the subtasks should also be deleted
                                (fails to delete issues with subtasks if not
                                set to True)
        :type  delete_subtasks: bool
        """
        query = {}
        if delete_subtasks is not None:
            query['deleteSubtasks'] = delete_subtasks

        self.delete('issue/{}'.format(issue_id), query=query)

    # search
    def search(
            self, jql, validate_query=None, fields=None, expand=None,
            properties=None, fields_by_keys=None, start_at=None,
            max_results=None):
        """
        Searches JIRA for issues using a JQL query.

        :param jql: JQL query string
        :type  jql: basestring
        :param validate_query: whether to validate the JQL query and how
                               strictly to validate (can be "strict", "warn",
                               "none", "true" or "false")
        :type  validate_query: basestring
        :param fields: list of fields to return for each issue
        :type  fields: basestring
        :param expand: comma-separated list of the parameters to expand
        :type  expand: basestring
        :param properties: list of properties to return for each issue
        :type  properties: basestring
        :param fields_by_keys: whether to reference fields in issues by keys
                               instead of ids
        :type  fields_by_keys: bool
        :param start_at: index in the collection to start at (defaults to 0)
        :type  start_at: int
        :param max_results: max number of resources to get (defaults to 50)
        :type  max_results: int
        :return: response containing JIRA search results
        :rtype: dict
        """
        query = {'jql': jql}
        if validate_query is not None:
            query['validateQuery'] = validate_query

        if fields is not None:
            query['fields'] = fields

        if expand is not None:
            query['expand'] = expand

        if properties is not None:
            query['properties'] = properties

        if fields_by_keys is not None:
            query['fieldsByKeys'] = fields_by_keys

        if start_at is not None:
            query['startAt'] = start_at

        if max_results is not None:
            query['maxResults'] = max_results

        return self.get('search', query=query).json()

    def complete_search(
            self, jql, validate_query=None, fields=None, expand=None,
            properties=None, fields_by_keys=None,
            batch_size=DEFAULT_BATCH_SIZE):
        """
        Searches JIRA for issues using a JQL query.

        :param jql: JQL query string
        :type  jql: basestring
        :param validate_query: whether to validate the JQL query and how
                               strictly to validate (can be "strict", "warn",
                               "none", "true" or "false")
        :type  validate_query: basestring
        :param fields: list of fields to return for each issue
        :type  fields: basestring
        :param expand: comma-separated list of the parameters to expand
        :type  expand: basestring
        :param properties: list of properties to return for each issue
        :type  properties: basestring
        :param fields_by_keys: whether to reference fields in issues by keys
                               instead of ids
        :type  fields_by_keys: bool
        :param batch_size: number of resources to get in each request
        :type  batch_size: int
        :return: all JIRA search results
        :rtype: dict
        """
        query = {'jql': jql}
        if validate_query is not None:
            query['validateQuery'] = validate_query

        if fields is not None:
            query['fields'] = fields

        if expand is not None:
            query['expand'] = expand

        if properties is not None:
            query['properties'] = properties

        if fields_by_keys is not None:
            query['fieldsByKeys'] = fields_by_keys

        return self.get_all(
            'issues',
            'search',
            query=query,
            batch_size=batch_size)
