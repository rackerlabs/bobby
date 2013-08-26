"""
Functions for actually doing things
"""

from twisted.internet import defer
from bobby import cass
from bobby.ele import MaasClient


class BobbyWorker(object):
    """Worker for doing tasks."""

    def __init__(self, db):
        self._db = db

    def _get_maas_client(self):
        # TODO: get the service catalog and auth token.
        return MaasClient({}, 'abc')

    def create_server(self, tenant_id, group_id, server):
        """Create a server, register it with MaaS."""
        maas_client = self._get_maas_client()
        d = maas_client.create_entity(server)

        def create_server_record(entity_id):
            return cass.create_server(self._db, tenant_id, server.get('uri'), entity_id, group_id)
        d.addCallback(create_server_record)

        def add_checks_and_alarms(_):
            # TODO: implement this.
            return defer.succeed(None)
        d.addCallback(add_checks_and_alarms)

        def add_policies_to_server(server):
            # TODO: implement this.
            return defer.succeed(server)
        return d.addCallback(add_policies_to_server)

    def apply_policies_to_server(self, tenant_id, group_id, server_id, entity_id, nplan_id):
        """ Apply policies to a new server """
        d = cass.get_policies_by_group_id(self._db, group_id)

        def proc_policies(policies):
            deferreds = [
                self.add_policy_to_server(tenant_id, policy['policyId'], server_id, entity_id,
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

    def create_group(self, tenant_id, group_id):
        """ Create a group """
        # TODO: get the service catalog and auth token
        maas_client = MaasClient({}, 'abc')
        d = maas_client.add_notification_and_plan()

        def create_group((notification_id, notification_plan_id)):
            return cass.create_group(self._db, group_id, tenant_id, notification_id, notification_plan_id)
        return d.addCallback(create_group)

    def apply_policy(self, tenant_id, group_id, policy_id, check_template, alarm_template, nplan_id):
        """Apply a new policy accross a group of servers"""
        d = cass.get_servers_by_group_id(self._db, tenant_id, group_id)

        def proc_servers(servers):
            deferreds = [
                self.add_policy_to_server(self._db, tenant_id, policy_id, server['serverId'], server['entityId'],
                                          check_template, alarm_template, nplan_id)
                for server in servers
            ]
            return defer.gatherResults(deferreds, consumeErrors=False)
        d.addCallback(proc_servers)
        d.addCallback(lambda _: None)
        return d

    def add_policy_to_server(self, tenant_id, policy_id, server_id, entity_id, check_template, alarm_template,
                             nplan_id):
        """Adds a single policy to a server"""
        # TODO: get the service catalog and auth token
        maas_client = MaasClient({}, 'abc')
        d = maas_client.add_check(policy_id, entity_id, check_template)

        def add_alarm(check):
            d = maas_client.add_alarm(policy_id, entity_id, nplan_id, check['id'], alarm_template)
            return d.addCallback(lambda alarm: (check['id'], alarm['id']))
        d.addCallback(add_alarm)

        def register_policy((check_id, alarm_id)):
            return cass.register_policy_on_server(self._db, policy_id, server_id, alarm_id, check_id)
        d.addCallback(register_policy)
        return d
