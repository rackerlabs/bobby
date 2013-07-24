"""Tests for bobby.views."""
import json
import StringIO

import mock
from twisted.internet import defer
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from bobby import views


class BobbyDummyRequest(DummyRequest):
    """Dummy request object."""

    def __init__(self, postpath, session=None, content=''):
        super(BobbyDummyRequest, self).__init__(postpath, session)
        self.content = StringIO.StringIO()
        self.content.write(content)
        self.content.seek(0)

    def URLPath(self):
        """Fake URLPath object."""
        FakeURLPath = mock.Mock(spec=['path'])
        FakeURLPath.path = self.postpath
        return FakeURLPath


class TestGetGroups(unittest.TestCase):
    """Test GET /{tenantId}/groups"""

    @mock.patch('bobby.cass.get_groups_by_tenant_id')
    def test_get_groups(self, get_groups_by_tenant_id):
        """Returns application/json of all groups."""
        groups = [
            {'groupId': 'abcdef',
             'links': [
                 {
                     'href': '/101010/groups/abcdef',
                     'rel': 'self'
                 }
             ],
             'notification': 'notification-ghi',
             'notificationPlan': 'notificationPlan-jkl',
             'tenantId': '101010'
             },

            {'groupId': 'fedcba',
             'links': [
                 {
                     'href': '/101010/groups/fedcba',
                     'rel': 'self'
                 }
             ],
             'notification': 'notification-igh',
             'notificationPlan': 'notificationPlan-lkj',
             'tenantId': '101010'
             }
        ]
        expected = {'groups': groups}
        get_groups_by_tenant_id.return_value = defer.succeed(groups)

        request = BobbyDummyRequest('/101010/groups')
        d = views.get_groups(request, '101010')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)
        get_groups_by_tenant_id.assert_called_once_with('101010')


class TestCreateGroup(unittest.TestCase):
    """Test POST /{tenantId}/groups"""

    @mock.patch('bobby.cass.create_group')
    def test_create_group(self, create_group):
        """POST to /{tenantId}/groups creates a new group."""
        expected = {
            'groupId': 'uvwxyz',
            'links': [{
                'href': '/101010/groups/uvwxyz',
                'rel': 'self'
            }],
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def',
            'tenantId': 'tenant-ghi'
        }
        group = expected.copy()
        del group['links']
        create_group.return_value = defer.succeed(group)

        request_json = {
            'groupId': 'uvwxyz',
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def'
        }
        request = BobbyDummyRequest('/101010/groups/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = views.create_group(request, '010101')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)
        create_group.assert_called_once_with(
            'uvwxyz', '010101', 'notification-abc', 'notification-def')


class TestGetGroup(unittest.TestCase):
    """Test GET /{tenantId}/groups/{groupId}"""

    @mock.patch('bobby.cass.get_group_by_id')
    def test_get_group(self, get_group_by_id):
        """Returns application/json of group representation."""
        expected = {
            'groupId': 'uvwxyz',
            'links': [{
                'href': '/101010/groups/uvwxyz',
                'rel': 'self'
            }],
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def',
            'tenantId': 'tenant-ghi'
        }
        group = expected.copy()
        del group['links']
        get_group_by_id.return_value = defer.succeed(group)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = views.get_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeleteGroup(unittest.TestCase):
    """Test DELETE /{tenantId}/groups/{groupId}"""

    @mock.patch('bobby.cass.delete_group')
    def test_delete_group(self, delete_group):
        """Deletes a server, returning a 204."""
        delete_group.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = views.delete_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_group.assert_called_once_with('101010', 'uvwxyz')


class TestGetServers(unittest.TestCase):
    """Test GET /{tenantId}/groups/{groupId}."""

    @mock.patch('bobby.cass.get_servers_by_group_id')
    def test_get_servers(self, get_servers_by_group_id):
        """Returns application/json of all servers owned by a group."""
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
        get_servers_by_group_id.return_value = defer.succeed(servers)

        request = BobbyDummyRequest('/101010/groups/group-def/servers')
        d = views.get_servers(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestCreateServer(unittest.TestCase):
    """Test POST /{tenantId}/groups"""

    @mock.patch('bobby.cass.create_server')
    def test_create_server(self, create_server):
        """POSTing application/json creates a server."""
        expected = {
            'entityId': 'entity-xyz',
            'groupId': 'group-uvw',
            'links': [
                {
                    'href': '/101010/groups/group-uvw/servers/server-rst',
                    'rel': 'self'
                }
            ],
            'serverId': 'server-rst',
        }
        server = expected.copy()
        del server['links']
        create_server.return_value = defer.succeed(server)

        request_json = {
            'entityId': 'entity-xyz',
            'serverId': 'server-rst',
            'serverPolicies': [
                {'policyId': 'policy-xyz',
                 'alarmId': 'alarm-rst',
                 'checkId': 'check-uvw'}
            ]
        }
        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = views.create_server(request, '101010', server['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestGetServer(unittest.TestCase):
    """Test GET /{tenantId}/groups/{groupId}/servers/{serverId}"""

    @mock.patch('bobby.cass.get_server_by_server_id')
    def test_get_server(self, get_server_by_server_id):
        """Return application/json server representation."""
        expected = {
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
        server = expected.copy()
        del server['links']
        get_server_by_server_id.return_value = defer.succeed(server)

        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/server-rst')
        d = views.get_server(request, '101010', server['groupId'], server['serverId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeleteServer(unittest.TestCase):
    """Test DELETE /{tenantId}/groups/{groupId}/servers/{serverId}"""

    @mock.patch('bobby.cass.delete_server')
    def test_delete_server(self, delete_server):
        """Deletes a server and returns 402."""
        delete_server.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/servers/opqrst')
        d = views.delete_server(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_server.assert_called_once_with('101010', 'opqrst')


class TestGetPolicies(unittest.TestCase):
    """Test GET /{tenantId}/groups/{groupId}."""

    @mock.patch('bobby.cass.get_policies_by_group_id')
    def test_get_policies(self, get_policies_by_group_id):
        """Returns application/json of all policies owned by a group."""
        policies = [
            {
                'alarmTemplate': '{alarmTemplate1}',
                'checkTemplate': '{checkTemplate1}',
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
                'alarmTemplate': '{alarmTemplate2}',
                'checkTemplate': '{checkTemplate2}',
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
        get_policies_by_group_id.return_value = defer.succeed(policies)

        request = BobbyDummyRequest('/101010/groups/group-def/policies')
        d = views.get_policies(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestCreatePolicy(unittest.TestCase):
    """Test POST /{tenantId}/groups/{groupId}/policies"""

    @mock.patch('bobby.cass.create_policy')
    def test_create_server(self, create_policy):
        """POSTing application/json creates a policy."""
        expected = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
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
        policy = expected.copy()
        del policy['links']
        create_policy.return_value = defer.succeed(policy)

        request_json = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
            'policyId': 'policy-abc'
        }
        request = BobbyDummyRequest('/101010/groups/group-def/policies/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = views.create_policy(request, '101010', policy['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestGetPolicy(unittest.TestCase):
    """Test GET /{tenantId}/groups/{groupId}/policies/{serverId}"""

    @mock.patch('bobby.cass.get_policy_by_policy_id')
    def test_get_server(self, get_policy_by_policy_id):
        """Return application/json policy representation."""
        expected = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
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
        policy = expected.copy()
        del policy['links']
        get_policy_by_policy_id.return_value = defer.succeed(policy)

        request = BobbyDummyRequest('/101010/groups/group-def/policies/policy-abc')
        d = views.get_policy(request, '101010', policy['groupId'], policy['policyId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeletePolicy(unittest.TestCase):
    """Test DELETE /{tenantId}/groups/{groupId}/policiess/{policyId}"""

    @mock.patch('bobby.cass.delete_policy')
    def test_delete_server(self, delete_policy):
        """Deletes a policy and returns 402."""
        delete_policy.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/policies/opqrst')
        d = views.delete_policy(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_policy.assert_called_once_with('opqrst')
