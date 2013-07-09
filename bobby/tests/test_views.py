import json

import mock
from twisted.internet import defer
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from bobby import views


class BobbyDummyContent(object):

    def __init__(self, content=''):
        self._content = content

    def read(self):
        return self._content


class BobbyDummyRequest(DummyRequest):

    def __init__(self, postpath, session=None, content=''):
        super(BobbyDummyRequest, self).__init__(postpath, session)
        self.content = BobbyDummyContent(content)


class DBTestCase(unittest.TestCase):

    def setUp(self):
        client_patcher = mock.patch('bobby.views.client', spec=['execute'])
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()


class GroupsTest(DBTestCase):
    '''Test /groups.'''

    def test_groups(self):
        expected = [
            {'groupId': 'abcdef',
             'webhook': '/a_webhook'},
            {'groupId': 'fedcba',
             'webhook': '/another_webhook'}
        ]

        def _execute(*args, **kwargs):
            return defer.succeed(expected)
        self.client.execute.side_effect = _execute

        request = BobbyDummyRequest('/groups')
        d = views.groups(request)

        def _assert(_):
            result = json.loads(request.written[0])
            self.assertEqual(result, expected)

            self.client.execute.assert_called_once_with(
                'SELECT * FROM GROUPS;', {}, 1)
        return d.addCallback(_assert)

    def test_group_update(self):
        self.client.execute.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/groups/0', content='webhook=/a')
        request.method = 'PUT'
        d = views.group_update(request, 0)

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'INSERT INTO groups ("groupId", "webhook") VALUES (:groupId, :webhook);',
                {'webhook': '/a', 'groupId': 0},
                1)
        return d.addCallback(_assert)

    def test_group_delete(self):
        self.client.execute.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/groups/0')
        request.method = 'DELETE'
        d = views.group_delete(request, 0)

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM groups WHERE "groupId"=:groupId;',
                {'webhook': None, 'groupId': 0},
                1)
        return d.addCallback(_assert)


class ServersTest(DBTestCase):
    '''Test /servers'''

    def test_servers(self):
        expected = [
            {'serverId': 1,
             'groupId': 'abcdef',
             'state': 'left'},
            {'serverId': 2,
             'groupId': 'fedcba',
             'state': 'right'},
        ]

        def execute(*args, **kwargs):
            return defer.succeed(expected)
        self.client.execute.side_effect = execute

        request = BobbyDummyRequest('/servers')
        d = views.servers(request)

        def _assert(_):
            result = json.loads(request.written[0])
            self.assertEqual(result, expected)

            self.client.execute.assert_called_once_with(
                'SELECT * FROM SERVERS;', {}, 1)
        return d.addCallback(_assert)

    def test_group_server_update(self):
        self.client.execute.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/groups/0/servers/1')
        request.method = 'PUT'
        d = views.group_server_update(request, "group-a", "server-b")

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'INSERT INTO servers ("serverId", "groupId", "state") VALUES (:serverId, :groupId, :webhook);',
                {'serverId': 'server-b', 'groupId': 'group-a', 'state': 'OK'},
                1)
        return d.addCallback(_assert)

    def test_group_server_delete(self):
        self.client.execute.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/groups/0/servers/1')
        request.method = 'DELETE'
        d = views.group_server_delete(request, 0, 1)

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM servers WHERE "serverId"=:serverId;',
                {'serverId': 1},
                1)
        return d.addCallback(_assert)

    def test_group_server_webhook(self):
        self.client.execute.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/groups/0/servers/1/webhook')
        request.method = 'POST'
        request.args['state'] = ['OK']
        d = views.group_server_webhook(request, 0, 1)

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'UPDATE servers SET "state"=:state WHERE "serverId"=:serverId AND "groupId"=:groupId;',
                {'serverId': 1, 'groupId': 0, 'state': False},
                1)
        return d.addCallback(_assert)
