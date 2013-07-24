"""
Functions for getting data out of Cassandra.
"""
from silverberg.client import ConsistencyLevel
from twisted.internet import defer


class ExcessiveResultsError(Exception):
    """Exception raised when too many results are found."""
    def __init__(self, type_string, type_id):
        super(ExcessiveResultsError, self).__init__(
            'Too many results found for type "{0}" and id "{1}"'.format(
                type_string, type_id))


class ResultNotFoundError(Exception):
    """Exception raised when a group is not found when querying Cassandra."""
    def __init__(self, type_string, type_id):
        super(ResultNotFoundError, self).__init__(
            'Result of type "{0}" and id "{1}" not found.'.format(type_string, type_id))


def get_groups_by_tenant_id(tenant_id):
    """Get all groups owned by a provided tenant."""
    query = 'SELECT * FROM groups WHERE "tenantId"=:tenantId;'
    return _client.execute(query, {'tenantId': tenant_id}, ConsistencyLevel.ONE)


def get_group_by_id(tenant_id, group_id):
    """Get a group by its id."""
    query = 'SELECT * FROM groups WHERE "groupId"=:groupId;'
    d = _client.execute(query, {'groupId': group_id}, ConsistencyLevel.ONE)

    def return_group(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('group', group_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('group', group_id))
        return defer.succeed(result[0])
    return d.addCallback(return_group)


def create_group(group_id, tenant_id, notification, notification_plan):
    """Create a new group and return that new group."""

    query = ' '.join([
            'INSERT INTO groups',
            '("groupId", "tenantId", "notification", "notificationPlan")',
            'VALUES (:groupId, :tenantId, :notification, :notificationPlan);'])

    data = {'groupId': group_id,
            'tenantId': tenant_id,
            'notification': notification,
            'notificationPlan': notification_plan}

    d = _client.execute(query, data, ConsistencyLevel.ONE)

    def retrieve_new_group(_):
        return get_group_by_id(tenant_id, group_id)
    return d.addCallback(retrieve_new_group)


def delete_group(tenant_id, group_id):
    """Delete a group."""
    query = 'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'
    return _client.execute(query,
                           {'groupId': group_id,
                           'tenantId': tenant_id},
                           ConsistencyLevel.ONE)


def get_servers_by_group_id(tenant_id, group_id):
    """Get all servers with a specified groupId."""
    query = 'SELECT * FROM servers WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'

    return _client.execute(query, {'groupId': group_id, 'tenantId': tenant_id},
                           ConsistencyLevel.ONE)


def get_server_by_server_id(tenant_id, server_id):
    """Get a server by its serverId."""

    query = 'SELECT * FROM servers WHERE "serverId"=:serverId AND "tenantId"=:tenantId;'

    d = _client.execute(query, {'serverId': server_id, 'tenantId': tenant_id},
                        ConsistencyLevel.ONE)

    def return_server(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('server', server_id))
        elif len(result) > 1:
            return defer.fail(ExcessiveResultsError('server', server_id))
        return defer.succeed(result[0])
    return d.addCallback(return_server)


def create_server(tenant_id, server_id, entity_id, group_id, server_policies):
    """Create and return a new server dict."""
    query = ' '.join([
        'INSERT INTO servers ("tenantId", "serverId", "entityId", "groupId")',
        'VALUES (:tenantId, :serverId, :entityId, :groupId);'])

    d = _client.execute(query,
                        {'serverId': server_id, 'entityId': entity_id, 'groupId': group_id,
                         'tenantId': tenant_id},
                        ConsistencyLevel.ONE)

    def retrieve_server(_):
        return get_server_by_server_id(tenant_id, server_id)
    return d.addCallback(retrieve_server)


def delete_server(tenant_id, server_id):
    """Delete a server and cascade to deleting related serverpolicies."""
    # TODO: also delete the entity is MaaS
    query = 'DELETE FROM servers WHERE "serverId"=:serverId AND "tenantId"=:tenantId;'
    d = _client.execute(query,
                        {'serverId': server_id, 'tenantId': tenant_id},
                        ConsistencyLevel.ONE)

    #def remove_server_policies(_):
        #query = 'DELETE FROM serverpolicies WHERE "serverId"=:serverId;'
        #return _client.execute(query, {'serverId': server_id}, ConsistencyLevel.ONE)
    #return d.addCallback(remove_server_policies)

    return d


def get_policies_by_group_id(group_id):
    """Get all policies owned by a provided groupId."""
    query = 'SELECT * FROM policies WHERE "groupId"=:groupId;'
    return _client.execute(query, {'groupId': group_id},
                           ConsistencyLevel.ONE)


def get_policy_by_policy_id(group_id, policy_id):
    """Get a single policy by its policyId."""
    query = 'SELECT * FROM policies WHERE "policyId"=:policyId AND "groupId"=:groupId;'

    d = _client.execute(query, {'policyId': policy_id, 'groupId': group_id}, ConsistencyLevel.ONE)

    def return_policy(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('policy', policy_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('policy', policy_id))
        return defer.succeed(result[0])
    return d.addCallback(return_policy)


def create_policy(policy_id, group_id, alarm_template, check_template):
    """Create and return a policy."""
    query = ' '.join((
        'INSERT INTO policies ("policyId", "groupId", "alarmTemplate", "checkTemplate")',
        'VALUES (:policyId, :groupId, :alarmTemplate, :checkTemplate);'
    ))

    d = _client.execute(query,
                        {'policyId': policy_id,
                         'groupId': group_id,
                         'alarmTemplate': alarm_template,
                         'checkTemplate': check_template},
                        ConsistencyLevel.ONE)

    def retrieve_policy(_):
        return get_policy_by_policy_id(group_id, policy_id)
    return d.addCallback(retrieve_policy)


def delete_policy(policy_id):
    """Delete a policy and associated serverpolicies."""
    query = 'DELETE FROM policies WHERE "policyId"=:policyId;'

    d = _client.execute(query,
                        {'policyId': policy_id},
                        ConsistencyLevel.ONE)

    # TODO: re-enable this. Cassandra's composite primary keys are a *real*
    # head scratcher.
    #def remove_server_policies(_):
    #    query = 'DELETE FROM serverpolicies WHERE "policyId"=:policyId;'
    #    return _client.execute(query, {'policyId': policy_id}, ConsistencyLevel.ONE)
    return d


_client = None


def set_client(client):
    """Set the CQLClient connection to use."""
    global _client
    _client = client
