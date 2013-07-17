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
            spec=['get_by_group_id', 'get_by_tenant_id', 'new'])
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

    def test_get_group(self):
        group_data = {
            'groupId': 'uvwxyz',
            'links': [
                {
                    'href': '/101010/groups/uvwxyz',
                    'rel': 'self'
                }
            ],
            'webhook': 'http://example.com/an_webhook'
        }
        group = mock.create_autospec(models.Group)
        group.group_id = group_data['groupId']
        group.webhook = group_data['webhook']
        self.Group.get_by_group_id.return_value = defer.succeed(group)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')

        d = views.get_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, group_data)

    def test_delete_group(self):
        self.Group.get_by_group_id.return_value = defer.succeed(self.group)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = views.delete_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        self.group.delete.assert_called_once_with()
