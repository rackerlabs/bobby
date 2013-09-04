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

    def create_group(self, tenant_id, group_id):
        """Create a group, and register a notification and notification plan."""
        maas_client = self._get_maas_client()
        d = maas_client.add_notification_and_plan()

        def create_group_in_db((notification, notification_plan)):
            return cass.create_group(
                self._db, tenant_id, group_id, notification, notification_plan)
        d.addCallback(create_group_in_db)

        return d

    def create_server(self, tenant_id, group_id, server):
        """Create a server, register it with MaaS."""
        maas_client = self._get_maas_client()
        d = maas_client.create_entity(server)

        def create_server_record(entity_id):
            return cass.create_server(self._db, tenant_id, server.get('uri'), entity_id, group_id)
        d.addCallback(create_server_record)

        def get_server(_):
            return cass.get_server_by_server_id(server.get('uri'))
        d.addCallback(get_server)

        def apply_policies(server):
            return self.apply_policies_to_server(
                tenant_id, group_id, server['serverId'], server['entityId'])
        return d.addCallback(apply_policies)

    def delete_server(self, tenant_id, group_id, server_id):
        """ Clean up a server's records """
        d = cass.get_server_by_server_id(self._db, tenant_id, group_id, server_id)

        def delete_entity(result):
            maas_client = self._get_maas_client()
            d = maas_client.delete_entity(result['entityId'])
            return d
        d.addCallback(delete_entity)

        def delete_server_from_db(_):
            return cass.delete_server(self._db, tenant_id, group_id, server_id)
        d.addCallback(delete_server_from_db)

        return d

    def apply_policies_to_server(self, tenant_id, group_id, server_id, entity_id):
        """ Apply policies to a new server """
        group = []
        d = cass.get_group_by_id(self._db, tenant_id, group_id)

        def get_policies(_group):
            group.append(_group)
            return cass.get_policies_by_group_id(self._db, group_id)
        d.addCallback(get_policies)

        def proc_policies(policies):
            deferreds = [
                self.add_policy_to_server(
                    tenant_id, policy['policyId'], server_id, entity_id,
                    policy['checkTemplate'], policy['alarmTemplate'],
                    group[0]['notificationPlan'])
                for policy in policies
            ]
            return defer.gatherResults(deferreds, consumeErrors=False)
        d.addCallback(proc_policies)
        d.addCallback(lambda _: defer.succeed(None))
        return d

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
        maas_client = self._get_maas_client()
        d = maas_client.add_check(policy_id, entity_id, check_template)

        def add_alarm(check):
            d = maas_client.add_alarm(policy_id, entity_id, nplan_id, check['id'], alarm_template)
            return d.addCallback(lambda alarm: (check['id'], alarm['id']))
        d.addCallback(add_alarm)

        def register_policy((check_id, alarm_id)):
            return cass.register_policy_on_server(self._db, policy_id, server_id, alarm_id, check_id)
        d.addCallback(register_policy)
        return d
