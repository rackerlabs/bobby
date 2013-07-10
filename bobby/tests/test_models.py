'''Tests for bobby.models.'''
import mock
from silverberg.client import CQLClient
from twisted.internet import defer
from twisted.trial import unittest

from bobby import models


class DBTestCase(unittest.TestCase):

    def setUp(self):
        #client_patcher = mock.patch('bobby.views.client', spec=['execute'])
        #self.addCleanup(client_patcher.stop)
        #self.client = client_patcher.start()
        self.client = mock.create_autospec(CQLClient)


class GroupTestCase(DBTestCase):
    '''Tests for bobby.models.Group.'''

    def test_all(self):
        '''Group.all returns all the groups.'''
        def execute(*args, **kwargs):
            expected = [{'webhook': u'abcdef', 'groupId': '1'}]
            return defer.succeed(expected)
        self.client.execute.side_effect = execute

        d = models.Group.all(self.client)

        def _assert(result):
            self.assertEqual(len(result), 1)
            group = result[0]
            self.assertEqual(group['webhook'], u'abcdef')
        d.addCallback(_assert)
        return d

    def test_save(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        group = models.Group('x', 'y', self.client)
        d = group.save()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'INSERT INTO groups ("groupId", "webhook") VALUES (:groupId, :webhook);',
                {'webhook': 'y', 'groupId': 'x'},
                1)
        d.addCallback(_assert)
        return d

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        group = models.Group('x', 'y', self.client)
        d = group.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM groups WHERE "groupId"=:groupId;',
                {'webhook': 'y', 'groupId': 'x'},
                1)
        d.addCallback(_assert)
        return d


class ServerTestCase(DBTestCase):
    '''Tests for bobby.models.Server.'''

    def test_all(self):
        '''Server.all returns all the groups.'''
        def execute(*args, **kwargs):
            expected = [
                {'serverId': '2', 'groupId': 'y', 'state': 'OK'},
                {'serverId': '1', 'groupId': 'x', 'state': 'OK'}]
            return defer.succeed(expected)
        self.client.execute.side_effect = execute

        d = models.Server.all(self.client)

        def _assert(result):
            self.assertEqual(len(result), 2)
            group = result[0]
            self.assertEqual(group['serverId'], u'2')
            self.assertEqual(group['groupId'], u'y')
            self.assertEqual(group['state'], u'OK')
        d.addCallback(_assert)
        return d

    def test_save(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server = models.Server('x', 'y', 'OK', self.client)
        d = server.save()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'INSERT INTO servers ("serverId", "groupId", "state") VALUES (:serverId, :groupId, :webhook);',
                {'serverId': 'x', 'groupId': 'y', 'state': 'OK'},
                1)
        d.addCallback(_assert)
        return d

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server = models.Server('x', 'y', 'OK', self.client)
        d = server.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM servers WHERE "serverId"=:serverId;',
                {'serverId': 'x'},
                1)
        d.addCallback(_assert)
        return d

    def test_update(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server = models.Server('x', 'y', 'OK', self.client)
        d = server.update()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'UPDATE servers SET "state"=:state WHERE "serverId"=:serverId AND "groupId"=:groupId;',
                {'serverId': 'x', 'groupId': 'y', 'state': 'OK'},
                1)
        d.addCallback(_assert)
        return d
