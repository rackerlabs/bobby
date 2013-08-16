"""Tests for bobby.worker."""
import json

import mock
from twisted.internet import defer
from twisted.trial import unittest

from bobby import ele


class TestEleApi(unittest.TestCase):
    """ Test ELE API calls """

    def test_add_alarm(self):
        """ Test add_alarm """
        ele.add_alarm('t1', 'p1', 'en1', 'ch1', 'ALARM DSL', 'np')

    def test_fetch_entity_by_uuid(self):
        """ Test fetch_entity_by_uuid """
        ele.fetch_entity_by_uuid('t1', 'p1', 's1')


class TestMaasClient(unittest.TestCase):
    """Test bobby.ele.MaasClient."""

    def setUp(self):
        service_catalog = [
            {u'endpoints': [{
                u'publicURL': u'https://monitoring.api.rackspacecloud.com/v1.0/101010',
                u'tenantId': u'675646'}],
             u'name': u'cloudMonitoring',
             u'type': u'rax:monitor'}]
        self.client = ele.MaasClient(service_catalog, 'auth-abc')

    def test_init(self):
        public_url = u'https://monitoring.api.rackspacecloud.com/v1.0/123'
        auth_token = u'auth-abcdef'
        service_catalog = [
            {u'endpoints': [{
                u'publicURL': public_url,
                u'tenantId': u'675646'}],
             u'name': u'cloudMonitoring',
             u'type': u'rax:monitor'}]
        client = ele.MaasClient(service_catalog, auth_token)

        self.assertEqual(public_url, client._endpoint)
        self.assertEqual(auth_token, auth_token)

    @mock.patch('bobby.ele.treq')
    def test_add_notification_and_plan(self, treq):
        """A notification and notification are created."""
        def post(url, headers, data):
            if 'notifications' in url:
                response = mock.Mock()
                response.code = 201
                response.headers.getRawHeaders.return_value = ['notification-abc']
                return defer.succeed(response)
            elif 'notification_plans' in url:
                response = mock.Mock()
                response.code = 201
                response.headers.getRawHeaders.return_value = ['notificationPlan-xyz']
                return defer.succeed(response)
            else:
                return defer.fail(None)
        treq.post.side_effect = post

        d = self.client.add_notification_and_plan()
        result = self.successResultOf(d)

        self.assertEqual(('notification-abc', 'notificationPlan-xyz'), result)

        calls = [
            mock.call(
                'https://monitoring.api.rackspacecloud.com/v1.0/101010/notifications',
                headers={'content-type': ['application/json'],
                         'accept': ['application/json'],
                         'x-auth-token': ['auth-abc']},
                data='{"type": "webhook", "details": {"url": "/alarm"}, "label": '
                     '"Auto Scale Webhook Notification"}'),
            mock.call(
                'https://monitoring.api.rackspacecloud.com/v1.0/101010/notification_plans',
                headers={'content-type': ['application/json'],
                         'accept': ['application/json'],
                         'x-auth-token': ['auth-abc']},
                data='{"ok_state": ["notification-abc"], '
                     '"critical_state": ["notification-abc"], '
                     '"label": "Auto Scale Notification Plan"}'
            )
        ]
        self.assertEqual(calls, treq.post.mock_calls)

    @mock.patch('bobby.ele.treq')
    def test_remove_notification_and_plan(self, treq):
        def delete(url, headers):
            response = mock.Mock()
            response.code = 204
            return defer.succeed(response)
        treq.delete.side_effect = delete

        d = self.client.remove_notification_and_plan(
            'notificationPlan-xyz', 'notification-abc')
        self.successResultOf(d)

        calls = [
            mock.call(
                'https://monitoring.api.rackspacecloud.com/v1.0/101010/'
                'notification_plans/notificationPlan-xyz',
                headers={'content-type': ['application/json'],
                         'accept': ['application/json'],
                         'x-auth-token': ['auth-abc']}),
            mock.call(
                'https://monitoring.api.rackspacecloud.com/v1.0/101010/'
                'notifications/notification-abc',
                headers={'content-type': ['application/json'],
                         'accept': ['application/json'],
                         'x-auth-token': ['auth-abc']})
        ]
        self.assertEqual(calls, treq.delete.mock_calls)

    @mock.patch('bobby.ele.treq')
    def test_add_check(self, treq):
        def post(url, headers, data=None):
            response = mock.Mock()
            response.code = 201
            response.headers.getRawHeaders.return_value = ['http://example.com']
            return defer.succeed(response)
        treq.post.side_effect = post

        def get(url, headers):
            response = mock.Mock()
            response.code = 200
            return defer.succeed(response)
        treq.get.side_effect = get

        check_template = json.dumps({
            'label': 'Monitoring check',
            'type': 'remote.http',
            'details': {
                'url': 'http://www.example.com/',
                'method': 'GET'
            },
            'monitoring_zones_poll': [
                'mzA'
            ],
            'timeout': 30,
            'period': 100,
            'target_alias': 'default'
        })

        d = self.client.add_check('policy-abc', 'entity-def', check_template)
        self.successResultOf(d)

        treq.post.assert_called_once_with(
            'https://monitoring.api.rackspacecloud.com/v1.0/101010'
            '/entities/entity-def/checks',
            headers={'content-type': ['application/json'],
                     'accept': ['application/json'],
                     'x-auth-token': ['auth-abc']},
            data='{"target_alias": "default", "period": 100, '
                 '"label": "Monitoring check", '
                 '"details": {"url": "http://www.example.com/", "method": "GET"}, '
                 '"timeout": 30, "monitoring_zones_poll": ["mzA"], '
                 '"type": "remote.http"}')
        treq.get.assert_called_once_with(
            'http://example.com',
            headers={'content-type': ['application/json'],
                     'accept': ['application/json'],
                     'x-auth-token': ['auth-abc']})

    @mock.patch('bobby.ele.treq')
    def test_remove_check(self, treq):
        def delete(url, headers):
            response = mock.Mock()
            response.code = 204
            return defer.succeed(response)
        treq.delete.side_effect = delete

        d = self.client.remove_check('entity-abc', 'check-xyz')
        self.successResultOf(d)

        treq.delete.assert_called_once_with(
            'https://monitoring.api.rackspacecloud.com/v1.0/101010'
            '/entities/entity-abc/checks/check-xyz',
            headers={'content-type': ['application/json'],
                     'accept': ['application/json'],
                     'x-auth-token': ['auth-abc']})
