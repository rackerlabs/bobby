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


def apply_policies_to_server(tenant_id, group_id, server_id, entity_id, nplan_id):
    """ Apply policies to a new server """
    d = cass.get_policies_by_group_id(group_id)

    def proc_policies(policies):
        deferreds = [
            add_policy_to_server(tenant_id, policy['policyId'], server_id, entity_id,
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
    # TODO: get the service catalog and auth token
    maas_client = ele.MaasClient({}, 'abc')
    d = maas_client.add_notification_and_plan()

    def create_group((notification_id, notification_plan_id)):
        return cass.create_group(group_id, tenant_id, notification_id, notification_plan_id)
    return d.addCallback(create_group)


def apply_policy(tenant_id, group_id, policy_id, check_template, alarm_template, nplan_id):
    """Apply a new policy accross a group of servers"""
    d = cass.get_servers_by_group_id(tenant_id, group_id)

    def proc_servers(servers):
        deferreds = [
            add_policy_to_server(tenant_id, policy_id, server['serverId'], server['entityId'],
                                 check_template, alarm_template, nplan_id)
            for server in servers
        ]
        return defer.gatherResults(deferreds, consumeErrors=False)
    d.addCallback(proc_servers)
    d.addCallback(lambda _: None)
    return d


def add_policy_to_server(tenant_id, policy_id, server_id, entity_id, check_template, alarm_template,
                         nplan_id):
    """Adds a single policy to a server"""
    # TODO: get the service catalog and auth token
    maas_client = ele.MaasClient({}, 'abc')
    d = maas_client.add_check(policy_id, entity_id, check_template)

    def add_alarm(check):
        d = maas_client.add_alarm(policy_id, entity_id, nplan_id, check['id'], alarm_template)
        return d.addCallback(lambda alarm: (check['id'], alarm['id']))
    d.addCallback(add_alarm)

    def register_policy((check_id, alarm_id)):
        return cass.register_policy_on_server(policy_id, server_id, alarm_id, check_id)
    d.addCallback(register_policy)
    return d
