import json

import mock
from twisted.internet import defer
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from bobby import models, views


class BobbyDummyContent(object):

    def __init__(self, content=''):
        self._content = content

    def read(self):
        return self._content


class BobbyDummyRequest(DummyRequest):

    def __init__(self, postpath, session=None, content=''):
        super(BobbyDummyRequest, self).__init__(postpath, session)
        self.content = BobbyDummyContent(content)


class GroupsTest(unittest.TestCase):
    '''Test /{tenantId}/groups'''

    def setUp(self):
        # Ew. Need to move that client connection out of views soon.
        client_patcher = mock.patch('bobby.views.client')
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()

        Group_patcher = mock.patch(
            'bobby.views.Group',
            spec=['get_by_tenant_id', 'new'])
        self.addCleanup(Group_patcher.stop)
        self.Group = Group_patcher.start()

        self.group = mock.create_autospec(models.Group)
        self.Group.return_value = self.group

    def test_get_groups(self):
        groups = [
            {'groupId': 'abcdef',
             'links': [
                 {
                     'href': '/101010/groups/abcdef',
                     'rel': 'self'
                 }
             ],
             'webhook': 'http://example.com/an_webhook1'
             },
            {'groupId': 'fedcba',
             'links': [
                 {
                     'href': '/101010/groups/fedcba',
                     'rel': 'self'
                 }
             ],
             'webhook': 'http://example.com/an_webhook2'
             }
        ]
        expected = {'groups': groups}
        self.Group.get_by_tenant_id.return_value = defer.succeed(groups)
        request = BobbyDummyRequest('/101010/groups')
        d = views.get_groups(request, '101010')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)

    def test_create_group(self):
        group_data = {
            'groupId': 'uvwxyz',
            'links': {
                'href': '/101010/groups/uvwxyz',
                'rel': 'self'
            },
            'webhook': 'http://example.com/an_webhook'
        }

        group = mock.create_autospec(models.Group)
        group.group_id = group_data['groupId']
        group.webhook = group_data['webhook']
        self.Group.new.return_value = defer.succeed(group)

        request = BobbyDummyRequest('/101010/groups/')
        request.method = 'POST'
        request.args['groupId'] = [group_data['groupId']]
        request.args['webhook'] = [group_data['webhook']]

        d = views.create_group(request, 010101)

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, group_data)


class GroupsTestOld(unittest.TestCase):
    '''Test /groups.'''

    def setUp(self):
        # Ew. Need to move that client connection out of views soon.
        client_patcher = mock.patch('bobby.views.client')
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()

        Group_patcher = mock.patch('bobby.views.Group')
        self.addCleanup(Group_patcher.stop)
        self.Group = Group_patcher.start()

        self.group = mock.MagicMock(spec=['delete', 'save'])
        self.group.delete.return_value = defer.succeed(None)
        self.group.save.return_value = defer.succeed(None)

        self.Group.return_value = self.group

    def test_groups(self):
        expected = [
            {'groupId': 'abcdef',
             'webhook': '/a_webhook'},
            {'groupId': 'fedcba',
             'webhook': '/another_webhook'}
        ]
        self.Group.all = mock.MagicMock(return_value=defer.succeed(expected))
        request = BobbyDummyRequest('/groups')
        d = views.groups(request)

        def _assert(_):
            result = json.loads(request.written[0])
            self.assertEqual(result, expected)

            self.Group.all.assert_called_once_with(self.client)
        return d.addCallback(_assert)

    def test_group_update(self):
        request = BobbyDummyRequest('/groups/0', content='webhook=/a')
        request.method = 'PUT'
        d = views.group_update(request, 0)

        def _assert(_):
            self.group.save.assert_called_once_with()
        return d.addCallback(_assert)

    def test_group_delete(self):
        request = BobbyDummyRequest('/groups/0')
        request.method = 'DELETE'
        d = views.group_delete(request, 0)

        def _assert(_):
            self.group.delete.assert_called_once_with()
        return d.addCallback(_assert)


class ServersTestOld(unittest.TestCase):
    '''Test /servers'''

    def setUp(self):
        # Ew. Need to move that client connection out of views soon.
        client_patcher = mock.patch('bobby.views.client')
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()

        Server_patcher = mock.patch('bobby.views.Server')
        self.addCleanup(Server_patcher.stop)
        self.Server = Server_patcher.start()

        self.server = mock.MagicMock(spec=['delete', 'save', 'update'])
        self.server.delete.return_value = defer.succeed(None)
        self.server.save.return_value = defer.succeed(None)

        self.Server.return_value = self.server

    def test_servers(self):
        expected = [
            {'serverId': 1,
             'groupId': 'abcdef',
             'state': 'left'},
            {'serverId': 2,
             'groupId': 'fedcba',
             'state': 'right'},
        ]
        self.Server.all = mock.MagicMock(return_value=defer.succeed(expected))

        request = BobbyDummyRequest('/servers')
        d = views.servers(request)

        def _assert(_):
            result = json.loads(request.written[0])
            self.assertEqual(result, expected)

            self.Server.all.assert_called_once_with(self.client)
        return d.addCallback(_assert)

    def test_group_server_update(self):
        request = BobbyDummyRequest('/groups/0/servers/1')
        request.method = 'PUT'
        d = views.group_server_update(request, "group-a", "server-b")

        def _assert(_):
            self.server.save.assert_called_once_with()
        return d.addCallback(_assert)

    def test_group_server_delete(self):
        request = BobbyDummyRequest('/groups/0/servers/1')
        request.method = 'DELETE'
        d = views.group_server_delete(request, 0, 1)

        def _assert(_):
            self.server.delete.assert_called_once_with()
        return d.addCallback(_assert)

    def test_group_server_webhook(self):
        request = BobbyDummyRequest('/groups/0/servers/1/webhook')
        request.method = 'POST'
        request.args['state'] = ['OK']
        d = views.group_server_webhook(request, 0, 1)

        def _assert(_):
            self.server.update.assert_called_once_with()
        return d.addCallback(_assert)
