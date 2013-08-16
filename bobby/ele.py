"""
In a time long ago, there was an asteroid heading towards our fair planet.
And so they needed a team of men to save us all.  Not just any men.  The best
astronauts.  The best drilling experts.  And a few extra characters to provide
comic relief.

But that's not what this is about.

This is about Rackspace Cloud Monitoring, nicknamed "ELE" for "Extinction
Level Event", because the design goal is that we should be able to survive
a direct asteroid hit on all but one data centers and then send you a small
number of helpful emails informing you that all of the servers it is aware
of have suddenly disappeared.

Sadly, this required servers that were equipped with robot arms and artificial
intelligence and would be able to shock to death the guy who was trying to
unplug the servers.  And that breaks several sections of the Geneva Convention.
So we make do with what we can.

And thus, we reach this piece of code, which is a super-lightweight facade for
the calls we'll make against MaaS.
"""
import json

from otter.util import http
import treq
from twisted.internet import defer


def add_check(tenant_id, policy_id, entity_id, check_template):
    """ Add a check to the MaaS system """
    return defer.fail(None)


def add_alarm(tenant_id, policy_id, entity_id, check_id, alarm_template, nplan_id):
    """ Add an alarm to the MaaS system """
    return defer.succeed('al')


def fetch_entity_by_uuid(tenant_id, policy_id, server_id):
    """ Fetch an entity by the UUID """
    pass


class MaasClient(object):
    """A web client for making requests to MaaS."""

    SERVICE_NAME = 'cloudMonitoring'

    def __init__(self, service_catalog, auth_token):
        # MaaS doesn't have regions.
        for service in service_catalog:
            if self.SERVICE_NAME == service['name']:
                self._endpoint = service['endpoints'][0]['publicURL']
                break
        self._auth_token = auth_token

    def add_notification_and_plan(self):
        """Groups must have a Notification and Notification plan for Auto
Scale.

        This should only have to be created for each group, and the ids should
        be stored in the database.
        """
        notification_id = []

        # TODO: Finish this path to the webhook
        notification_data = {
            'label': 'Auto Scale Webhook Notification',
            'type': 'webhook',
            'details': {
                'url': '/alarm'
            }
        }
        notification_url = http.append_segments(self._endpoint, 'notifications')
        d = treq.post(notification_url,
                      headers=http.headers(self._auth_token),
                      data=json.dumps(notification_data))
        d.addCallback(http.check_success, [201])

        # Get the newly created notification
        def create_notification_plan(result):
            not_id = result.headers.getRawHeaders('x-object-id')[0]
            notification_id.append(not_id)

            notification_plan_data = {
                'label': 'Auto Scale Notification Plan',
                'critical_state': [not_id],
                'ok_state': [not_id]
            }
            notification_plan_url = http.append_segments(
                self._endpoint, 'notification_plans')
            return treq.post(notification_plan_url,
                             headers=http.headers(self._auth_token),
                             data=json.dumps(notification_plan_data))
        d.addCallback(create_notification_plan)
        d.addCallback(http.check_success, [201])

        def return_ids(result):
            notification_plan_id = result.headers.getRawHeaders('x-object-id')[0]
            return defer.succeed((notification_id[0], notification_plan_id))
        return d.addCallback(return_ids)

    def remove_notification_and_plan(self, notification_plan_id, notification_id):
        """Delete a notification plan and notification id."""
        notification_plan_url = http.append_segments(
            self._endpoint, 'notification_plans', notification_plan_id)
        d = treq.delete(notification_plan_url,
                        headers=http.headers(self._auth_token))
        d.addCallback(http.check_success, [204])

        def delete_notification(_):
            notification_url = http.append_segments(
                self._endpoint, 'notifications', notification_id)
            return treq.delete(notification_url,
                               headers=http.headers(self._auth_token))
        d.addCallback(delete_notification)
        d.addCallback(http.check_success, [204])
        return d

    def add_check(self, policy_id, entity_id, check_template):
        """Add a new check to the entity."""
        d = treq.post(
            http.append_segments(self._endpoint, 'entities', entity_id, 'checks'),
            headers=http.headers(self._auth_token),
            data=check_template)
        d.addCallback(http.check_success, [201])

        def get_check(result):
            location = result.headers.getRawHeaders('Location')[0]
            return treq.get(location, headers=http.headers(self._auth_token))
        d.addCallback(get_check)
        d.addCallback(http.check_success, [200])
        return d.addCallback(treq.json_content)

    def remove_check(self, entity_id, check_id):
        """Remove a check."""
        d = treq.delete(http.append_segments(
            self._endpoint, 'entities', entity_id, 'checks', check_id),
            headers=http.headers(self._auth_token))
        return d.addCallback(http.check_success, [204])
