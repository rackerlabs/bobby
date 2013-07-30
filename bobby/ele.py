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

from twisted.internet import defer


def add_check(tenant_id, policy_id, server_id, check_template):
    """ Add a check to the MaaS system """
    return defer.succeed('ch')


def add_alarm(tenant_id, policy_id, server_id, check_id, alarm_template, nplan_id):
    """ Add an alarm to the MaaS system """
    return defer.succeed('al')


def add_notification(tenant_id):
    """ Add a notification to the MaaS system """
    return defer.succeed('no')


def add_notification_plan(tenant_id, notification):
    """ Add a notification plan to the MaaS system """
    return defer.succeed('np')


def fetch_entity_by_uuid(tenant_id, policy_id, server_id):
    """ Fetch an entity by the UUID """
    pass
