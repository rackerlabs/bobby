"""
Functions for actually doing things
"""

from twisted.internet import defer
from bobby import ele, cass


def create_server_entity(tenant_id, policy_id, server_id):
    """ Creates a server's entity in MaaS """
    ele.fetch_entity_by_uuid(tenant_id, policy_id, server_id)
    apply_policies_to_server(tenant_id, server_id)
    return defer.succeed(None)


def apply_policies_to_server(tenant_id, group_id, server_id, nplan_id):
    """ Apply policies to a new server """
    d = cass.get_policies_by_group_id(group_id)

    def proc_policies(policies):
        deferreds = [
            add_policy_to_server(tenant_id, policy['policyId'], server_id,
                                 policy['checkTemplate'], policy['alarmTemplate'], nplan_id)
            for policy in policies
        ]
        return defer.gatherResults(deferreds, consumeErrors=False)
    d.addCallback(proc_policies)
    d.addCallback(lambda _: None)
    return d

# Commented out so as to not screw up lint
#def remove_server(tenant_id, server_id):
#   """ Clean up a server's records """
#   pass


def create_group(tenant_id, group_id):
    """ Create a group """
    d = ele.add_notification(tenant_id)

    def post_add_notification(notification_id):
        d = ele.add_notification_plan(tenant_id, notification_id)
        d.addCallback(lambda nplan_id: (notification_id, nplan_id))
        return d
    d.addCallback(post_add_notification)

    def create_group(results):
        notification_id, nplan_id = results
        d = cass.create_group(group_id, tenant_id, notification_id, nplan_id)
        return d

    d.addCallback(create_group)
    return d


def apply_policy(tenant_id, group_id, policy_id, check_template, alarm_template, nplan_id):
    """Apply a new policy accross a group of servers"""
    d = cass.get_servers_by_group_id(tenant_id, group_id)

    def proc_servers(servers):
        deferreds = [
            add_policy_to_server(tenant_id, policy_id, server['serverId'], check_template,
                                 alarm_template, nplan_id)
            for server in servers
        ]
        return defer.gatherResults(deferreds, consumeErrors=False)
    d.addCallback(proc_servers)
    d.addCallback(lambda _: None)
    return d


def add_policy_to_server(tenant_id, policy_id, server_id, check_template, alarm_template, nplan_id):
    """Adds a single policy to a server"""
    d = ele.add_check(tenant_id, policy_id, server_id, check_template)

    def add_alarm(check_id):
        d = ele.add_alarm(tenant_id, policy_id, server_id, check_id, alarm_template, nplan_id)
        d.addCallback(lambda alarm_id: (check_id, alarm_id))
        return d
    d.addCallback(add_alarm)

    def register_policy(res):
        check_id, alarm_id = res
        cass.register_policy_on_server(policy_id, server_id, alarm_id, check_id)
    d.addCallback(register_policy)
    return d