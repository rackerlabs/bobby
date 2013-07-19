'''
Functions for getting data out of Cassandra.
'''
from silverberg.client import ConsistencyLevel
from twisted.internet import defer


class ExcessiveResultsError(Exception):
    '''Exception raised when too many results are found.'''
    def __init__(self, type_string, type_id):
        super(ExcessiveResultsError, self).__init__(
            'Too many results found for type "{0}" and id "{1}"'.format(
                type_string, type_id))


class GroupNotFound(Exception):
    '''Exception raised when a group is not found when querying Cassandra.'''
    def __init__(self, group_id):
        super(GroupNotFound, self).__init__(
            'Group {0} not found.'.format(group_id))


def get_groups_by_tenant_id(client, tenant_id):
    '''Get all groups owned by a provided tenant.'''
    query = 'SELECT * FROM groups WHERE "tenantId"=:tenantId ALLOW FILTERING;'
    return client.execute(query, {'tenantId': tenant_id}, ConsistencyLevel.ONE)


def get_group_by_id(client, group_id):
    '''Get a group by its id.'''
    query = 'SELECT * FROM groups WHERE "groupId"=:groupId;'
    d = client.execute(query, {'groupId': group_id}, ConsistencyLevel.ONE)

    def return_group(result):
        if len(result) < 1:
            return defer.fail(GroupNotFound(group_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('group', group_id))
        return defer.succeed(result[0])
    return d.addCallback(return_group)


def create_group(client, group_id, tenant_id, notification, notification_plan):
    '''Create a new group and return that new group.'''

    query = ' '.join([
            'INSERT INTO groups',
            '("groupId", "tenantId", "notification", "notificationPlan")',
            'VALUES (:groupId, :tenantId, :notification, :notificationPlan);'])

    data = {'groupId': group_id,
            'tenantId': tenant_id,
            'notification': notification,
            'notificationPlan': notification_plan}

    d = client.execute(query, data, ConsistencyLevel.ONE)

    def retrieve_new_group(_):
        return get_group_by_id(client, group_id)
    return d.addCallback(retrieve_new_group)


def delete_group(client, group_id):
    '''Delete a group.'''
    query = 'DELETE FROM groups WHERE "groupId"=:groupId;'
    return client.execute(query,
                          {'groupId': group_id},
                          ConsistencyLevel.ONE)
