# Copyright 2013 Rackspace, Inc.
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


def get_groups_by_tenant_id(db, tenant_id):
    """Get all groups owned by a provided tenant."""
    query = 'SELECT * FROM groups WHERE "tenantId"=:tenantId;'
    return db.execute(query, {'tenantId': tenant_id}, ConsistencyLevel.ONE)


def get_group_by_id(db, tenant_id, group_id):
    """Get a group db, by its id."""
    query = 'SELECT * FROM groups WHERE "tenantId"=:tenantId AND "groupId"=:groupId;'
    d = db.execute(query,
                   {'tenantId': tenant_id, 'groupId': group_id},
                   ConsistencyLevel.ONE)

    def return_group(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('group', group_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('group', group_id))
        return defer.succeed(result[0])
    return d.addCallback(return_group)


def create_group(db, tenant_id, group_id, notification, notification_plan):
    """Create a new group and return that new group."""

    query = ' '.join([
            'INSERT INTO groups',
            '("tenantId", "groupId", "notification", "notificationPlan")',
            'VALUES (:tenantId, :groupId, :notification, :notificationPlan);'])

    data = {'groupId': group_id,
            'tenantId': tenant_id,
            'notification': notification,
            'notificationPlan': notification_plan}

    d = db.execute(query, data, ConsistencyLevel.ONE)

    def retrieve_new_group(_):
        return get_group_by_id(db, tenant_id, group_id)
    return d.addCallback(retrieve_new_group)


def delete_group(db, tenant_id, group_id):
    """Delete a group."""
    query = 'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'
    return db.execute(query,
                      {'groupId': group_id,
                      'tenantId': tenant_id},
                      ConsistencyLevel.ONE)


def get_servers_by_group_id(db, tenant_id, group_id):
    """Get all servers with a specified groupId."""
    query = 'SELECT * FROM servers WHERE "groupId"=:groupId;'

    return db.execute(query, {'groupId': group_id},
                      ConsistencyLevel.ONE)


def get_server_by_server_id(db, tenant_id, group_id, server_id):
    """Get a server by its serverId."""

    query = 'SELECT * FROM servers WHERE "groupId"=:groupId AND "serverId"=:serverId;'

    d = db.execute(query, {'serverId': server_id, 'groupId': group_id},
                   ConsistencyLevel.ONE)

    def return_server(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('server', server_id))
        elif len(result) > 1:
            return defer.fail(ExcessiveResultsError('server', server_id))
        return defer.succeed(result[0])
    return d.addCallback(return_server)


# TODO: the order of these arguments makes almost no sense. Fix it plz.
def create_server(db, tenant_id, server_id, entity_id, group_id):
    """Create and return a new server dict."""
    query = ' '.join([
        'INSERT INTO servers ("serverId", "entityId", "groupId")',
        'VALUES (:serverId, :entityId, :groupId);'])

    d = db.execute(query,
                   {'serverId': server_id, 'entityId': entity_id, 'groupId': group_id},
                   ConsistencyLevel.ONE)

    def retrieve_server(_):
        return get_server_by_server_id(db, tenant_id, group_id, server_id)
    return d.addCallback(retrieve_server)


def delete_server(db, tenant_id, group_id, server_id):
    """Delete a server and cascade to deleting related serverpolicies."""
    # TODO: also delete the entity is MaaS
    query = 'DELETE FROM servers WHERE "groupId"=:groupId AND "serverId"=:serverId;'
    d = db.execute(query,
                   {'serverId': server_id, 'groupId': group_id},
                   ConsistencyLevel.ONE)

    return d


def get_policies_by_group_id(db, group_id):
    """Get all policies owned by a provided groupId."""
    query = 'SELECT * FROM policies WHERE "groupId"=:groupId;'
    return db.execute(query, {'groupId': group_id},
                      ConsistencyLevel.ONE)


def get_policy_by_policy_id(db, group_id, policy_id):
    """Get a single policy by its policyId."""
    query = 'SELECT * FROM policies WHERE "policyId"=:policyId AND "groupId"=:groupId;'

    d = db.execute(query, {'policyId': policy_id, 'groupId': group_id}, ConsistencyLevel.ONE)

    def return_policy(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('policy', policy_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('policy', policy_id))
        return defer.succeed(result[0])
    return d.addCallback(return_policy)


def create_policy(db, policy_id, group_id, alarm_template, check_template):
    """Create and return a policy."""
    query = ' '.join((
        'INSERT INTO policies ("policyId", "groupId", "alarmTemplate", "checkTemplate")',
        'VALUES (:policyId, :groupId, :alarmTemplate, :checkTemplate);'
    ))

    d = db.execute(query,
                   {'policyId': policy_id,
                    'groupId': group_id,
                    'alarmTemplate': alarm_template,
                    'checkTemplate': check_template},
                   ConsistencyLevel.ONE)

    def retrieve_policy(_):
        return get_policy_by_policy_id(db, group_id, policy_id)
    return d.addCallback(retrieve_policy)


def delete_policy(db, group_id, policy_id):
    """Delete a policy and associated serverpolicies."""
    query = 'DELETE FROM policies WHERE "groupId"=:groupId AND "policyId"=:policyId;'

    d = db.execute(query,
                   {'groupId': group_id,
                    'policyId': policy_id},
                   ConsistencyLevel.ONE)

    return d


def register_policy_on_server(db, policy_id, server_id, alarm_id, check_id):
    """Create a serverpolicy."""
    query = ' '.join((
        'INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", state)',
        'VALUES (:serverId, :policyId, :alarmId, :checkId, false);'
    ))

    d = db.execute(query,
                   {'policyId': policy_id,
                    'serverId': server_id,
                    'alarmId': alarm_id,
                    'checkId': check_id},
                   ConsistencyLevel.ONE)
    return d


def deregister_policy_on_server(db, policy_id, server_id):
    """Delete a serverpolicy record."""
    query = 'DELETE FROM serverpolicies WHERE "policyId"=:policyId AND "serverId"=:serverId;'

    d = db.execute(query,
                   {'policyId': policy_id,
                    'serverId': server_id},
                   ConsistencyLevel.ONE)

    return d


def get_policy_state(db, policy_id):
    """ Get the state of the policy checks on each server. """
    query = 'SELECT * FROM serverpolicies WHERE "policyId"=:policyId;'
    return db.execute(query, {'policyId': policy_id},
                      ConsistencyLevel.ONE)


def get_serverpolicies_by_server_id(db, group_id, server_id):
    """Get all serverpolicies for a server."""
    query = 'SELECT * FROM policies WHERE "groupId"=:groupId'
    d = db.execute(query,
                   {'groupId': group_id},
                   ConsistencyLevel.ONE)

    def find_server_policies(policies):
        policy_list = [policy['policyId'] for policy in policies]
        query = 'SELECT * FROM serverpolicies WHERE "policyId" IN (:policies) AND "serverId"=:serverId'
        return db.execute(query,
                          {'policies': ', '.join(policy_list),
                           'serverId': server_id},
                          ConsistencyLevel.ONE)
    return d.addCallback(find_server_policies)


def add_serverpolicy(db, server_id, policy_id):
    """Add a serverpolicy with the given server_id and policy_id.

    :param str server_id: A server_id
    :param str policy_id: A policy_id
    """
    # TODO: validate that the policy exists and belongs to the user.
    query = 'INSERT INTO serverpolicies ("serverId", "policyId") VALUES (:serverId, :policyId);'

    d = db.execute(query,
                   {'serverId': server_id, 'policyId': policy_id},
                   ConsistencyLevel.ONE)
    return d


def delete_serverpolicy(db, server_id, policy_id):
    """Delete a serverpolicy with the given server_id and policy_id.

    :param str server_id: A server_id
    :param str policy_id: A policy_id
    """
    query = 'DELETE FROM serverpolicies WHERE "serverId"=:serverId AND "policyId"=:policyId;'

    d = db.execute(query,
                   {'serverId': server_id, 'policyId': policy_id},
                   ConsistencyLevel.ONE)
    return d


def alter_alarm_state(db, alarm_id, state):
    """
    Get the alarm locator and alter the state for that alarm.

    This is slightly more complex than it needs to be because you can't do an UPDATE
    based on an index.... so we have to look up the serverpolicies record from
    the alarmId and then alter it.

    Remember: CQL looks like SQL but it isn't.  There is no query planner.
    """
    query = 'SELECT * FROM serverpolicies WHERE "alarmId"=:alarmId;'

    d = db.execute(query,
                   {'alarmId': alarm_id},
                   ConsistencyLevel.ONE)

    def do_alteration(result):
        if len(result) < 1:
            return defer.fail(ResultNotFoundError('alarm', alarm_id))
        if len(result) > 1:
            return defer.fail(ExcessiveResultsError('alarm', alarm_id))
        query = ('UPDATE serverpolicies SET state=:state WHERE "policyId"=:policyId '
                 'AND "serverId"=:serverId;')
        d2 = db.execute(query,
                        {'state': state,
                         'policyId': result[0]['policyId'],
                         'serverId': result[0]['serverId']},
                        ConsistencyLevel.ONE)
        d2.addCallback(lambda _: (result[0]['policyId'], result[0]['serverId']))
        return d2

    d.addCallback(do_alteration)

    return d


def check_quorum_health(db, policy_id):
    """
    Check the status of an alarm across all servers.

    :param policy_id: The id of the policy that needs a health check.
    :return: True if the quorum is healthy, False if the quorum is unhealthy.
    """
    query = ('SELECT * FROM serverpolicies WHERE "policyId"=:policyId;')
    d = db.execute(query,
                   {'policyId': policy_id},
                   ConsistencyLevel.ONE)

    def verify_health(serverpolicies):
        total = len(serverpolicies)
        critical = len([serverpolicy for serverpolicy in serverpolicies
                        if serverpolicy['state'] != 'OK'])

        if critical >= total / 2.0:
            return defer.succeed(False)
        else:
            return defer.succeed(True)
    return d.addCallback(verify_health)
