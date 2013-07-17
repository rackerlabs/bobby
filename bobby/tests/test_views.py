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


class ServersTest(unittest.TestCase):
    '''Test /{tenantId}/groups/{groupId}/servers'''

    def setUp(self):
        # Ew. Need to move that client connection out of views soon.
        client_patcher = mock.patch('bobby.views.client')
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()

        Server_patcher = mock.patch(
            'bobby.views.Server',
            spec=['get_all_by_group_id', 'get_by_server_id', 'new'])
        self.addCleanup(Server_patcher.stop)
        self.Server = Server_patcher.start()

        self.server = mock.create_autospec(models.Server)
        self.Server.return_value = self.server
        self.Server.new.return_value = defer.succeed(self.server)

    def test_get_servers(self):
        servers = [
            {'entityId': 'entity-abc',
             'groupId': 'group-def',
             'links': [
                 {
                     'href': '/101010/groups/group-def/servers/server-ghi',
                     'rel': 'self'
                 }
             ],
             'serverId': 'server-ghi'},
            {'entityId': 'entity-jkl',
             'groupId': 'group-def',
             'links': [
                 {
                     'href': '/101010/groups/group-def/servers/server-mno',
                     'rel': 'self'
                 }
             ],
             'serverId': 'server-mno'},
        ]
        expected = {'servers': servers}
        self.Server.get_all_by_group_id.return_value = defer.succeed(servers)
        request = BobbyDummyRequest('/101010/groups/group-def/servers')
        d = views.get_servers(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)

    def test_create_server(self):
        server_data = {
            'entityId': 'entity-xyz',
            'groupId': 'group-uvw',
            'links': [
                {
                    'href': '/101010/groups/group-uvw/servers/server-rst',
                    'rel': 'self'
                }
            ],
            'serverId': 'server-rst'
        }

        self.server.entity_id = server_data['entityId']
        self.server.group_id = server_data['groupId']
        self.server.server_id = server_data['serverId']

        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/')
        request.method = 'POST'
        request.args['entityId'] = [server_data['entityId']]
        request.args['serverId'] = [server_data['serverId']]

        d = views.create_server(request, '101010', server_data['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, server_data)

    def test_get_server(self):
        server_data = {
            'entityId': 'entity-xyz',
            'groupId': 'group-uvw',
            'links': [
                {
                    'href': '/101010/groups/group-uvw/servers/server-rst',
                    'rel': 'self'
                }
            ],
            'serverId': 'server-rst'
        }
        self.server.entity_id = server_data['entityId']
        self.server.group_id = server_data['groupId']
        self.server.server_id = server_data['serverId']
        self.Server.get_by_server_id.return_value = defer.succeed(self.server)

        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/server-rst')
        d = views.get_server(request, '101010', server_data['groupId'], server_data['serverId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, server_data)

    def test_delete_server(self):
        self.Server.get_by_server_id.return_value = defer.succeed(self.server)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/servers/opqrst')
        d = views.delete_server(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        self.server.delete.assert_called_once_with()


class PoliciesTest(unittest.TestCase):
    '''Test /{tenantId}/groups/{groupId}/servers'''

    def setUp(self):
        # Ew. Need to move that client connection out of views soon.
        client_patcher = mock.patch('bobby.views.client')
        self.addCleanup(client_patcher.stop)
        self.client = client_patcher.start()

        Policy_patcher = mock.patch(
            'bobby.views.Policy',
            spec=['get_all_by_group_id', 'get_by_policy_id', 'new'])
        self.addCleanup(Policy_patcher.stop)
        self.Policy = Policy_patcher.start()

        self.policy = mock.create_autospec(models.Policy)
        self.Policy.return_value = self.policy
        self.Policy.get_by_policy_id.return_value = defer.succeed(self.policy)
        self.Policy.new.return_value = defer.succeed(self.policy)

    def test_get_policies(self):
        policies = [
            {
                'alarmTemplateId': '{alarmTemplateId1}',
                'checkTemplateId': '{checkTemplateId1}',
                'groupId': '{groupId}',
                'links': [
                    {
                        'href':
                        '{url_root}/v1.0/{tenantId}/groups/{groupId}/policies/{policyId1}',
                        'rel': 'self'
                    }
                ],
                'policyId': '{policyId1}'
            },
            {
                'alarmTemplateId': '{alarmTemplateId2}',
                'checkTemplateId': '{checkTemplateId2}',
                'groupId': '{groupId}',
                'links': [
                    {
                        'href':
                        '{url_root}/v1.0/{tenantId}/groups/{groupId}/policies/{policyId2}',
                        'rel': 'self'
                    }
                ],
                'policyId': '{policyId2}'
            }
        ]
        expected = {'policies': policies}
        self.Policy.get_all_by_group_id.return_value = defer.succeed(policies)

        request = BobbyDummyRequest('/101010/groups/group-def/policies')
        d = views.get_policies(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)

    def test_create_policy(self):
        policy_data = {
            'alarmTemplateId': 'alarm-template-jkl',
            'checkTemplateId': 'check-template-ghi',
            'groupId': 'group-def',
            'links': [
                {
                    'href':
                    '/101010/groups/group-def/policies/policy-abc',
                    'rel': 'self'
                }
            ],
            'policyId': 'policy-abc'
        }

        self.policy.alarm_template_id = policy_data['alarmTemplateId']
        self.policy.check_template_id = policy_data['checkTemplateId']
        self.policy.group_id = policy_data['groupId']
        self.policy.policy_id = policy_data['policyId']

        request = BobbyDummyRequest('/101010/groups/group-def/policies/')
        request.method = 'POST'
        request.args['alarmTemplateId'] = [policy_data['alarmTemplateId']]
        request.args['checkTemplateId'] = [policy_data['checkTemplateId']]
        request.args['policyId'] = [policy_data['policyId']]

        d = views.create_policy(request, '101010', policy_data['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, policy_data)

    def test_get_policy(self):
        policy_data = {
            'alarmTemplateId': 'alarm-template-jkl',
            'checkTemplateId': 'check-template-ghi',
            'groupId': 'group-def',
            'links': [
                {
                    'href':
                    '/101010/groups/group-def/policies/policy-abc',
                    'rel': 'self'
                }
            ],
            'policyId': 'policy-abc'
        }

        self.policy.alarm_template_id = policy_data['alarmTemplateId']
        self.policy.check_template_id = policy_data['checkTemplateId']
        self.policy.group_id = policy_data['groupId']
        self.policy.policy_id = policy_data['policyId']

        request = BobbyDummyRequest('/101010/groups/group-def/policies/policy-abc')
        d = views.get_policy(request, '101010', policy_data['groupId'], policy_data['policyId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, policy_data)

    def test_delete_policy(self):
        request = BobbyDummyRequest('/101010/groups/uvwxyz/policies/opqrst')
        d = views.delete_policy(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        self.policy.delete.assert_called_once_with()
