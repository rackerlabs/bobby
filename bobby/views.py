import json

from klein import Klein
from silverberg.client import CQLClient
from twisted.internet import endpoints, reactor

from bobby.models import Group, Policy, Server

app = Klein()
client = CQLClient(
    endpoints.clientFromString(
        reactor,
        "tcp:{0}:{1}".format('localhost', 9160)),
    'bobby')


@app.route('/<string:tenant_id>/groups', methods=['GET'])
def get_groups(request, tenant_id):
    d = Group.get_all_by_tenant_id(client, tenant_id)

    def _return_result(groups):
        result = {'groups': groups}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)


@app.route('/<string:tenant_id>/groups', methods=['POST'])
def create_group(request, tenant_id):
    content = json.loads(request.content.read())
    group_id = content.get('groupId')
    notification = content.get('notification')
    notification_plan = content.get('notificationPlan')

    d = Group.new(client, group_id, tenant_id, notification, notification_plan)

    def _serialize_object(group):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'groupId': group.group_id,
            'links': [{
                'href': '{0}{1}'.format(request.URLPath().path, group.group_id),
                'rel': 'self'
            }],
            'notification': group.notification,
            'notificationPlan': group.notification_plan,
            'tenantId': group.tenant_id
        }
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(201)
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(_serialize_object)


@app.route('/<string:tenant_id>/groups/<string:group_id>', methods=['GET'])
def get_group(request, tenant_id, group_id):
    d = Group.get_by_group_id(client, tenant_id, group_id)

    def serialize_group(group):
        json_object = {
            'groupId': group.group_id,
            'links': [{
                'href': '{0}'.format(request.URLPath().path),
                'rel': 'self'
            }],
            'notification': group.notification,
            'notificationPlan': group.notification_plan,
            'tenantId': group.tenant_id
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize_group)


@app.route('/<string:tenant_id>/groups/<string:group_id>', methods=['DELETE'])
def delete_group(request, tenant_id, group_id):
    d = Group.get_by_group_id(client, tenant_id, group_id)

    def delete_group(group):
        return group.delete()
    d.addCallback(delete_group)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers', methods=['GET'])
def get_servers(request, tenant_id, group_id):
    d = Server.get_all_by_group_id(client, tenant_id, group_id)

    def serialize(servers):
        result = {'servers': servers}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers', methods=['POST'])
def create_server(request, tenant_id, group_id):
    content = json.loads(request.content.read())
    server_id = content.get('serverId')
    entity_id = content.get('entityId')

    try:
        server_policies = content.get('serverPolicies')
    except TypeError:
        server_policies = []

    d = Server.new(client, server_id, entity_id, group_id, server_policies)

    def serialize(server):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'entityId': server.entity_id,
            'groupId': server.group_id,
            'links': [
                {
                    'href': '{0}{1}'.format(request.URLPath().path, server.server_id),
                    'rel': 'self'
                }
            ],
            'serverId': server.server_id
        }

        d = server.view_policies()

        def add_policies_and_finish(policies):
            json_object['serverPolicies'] = policies
            request.setHeader('Content-Type', 'application/json')
            request.setResponseCode(201)
            request.write(json.dumps(json_object))
            request.finish()
        return d.addCallback(add_policies_and_finish)
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers/<string:server_id>', methods=['GET'])
def get_server(request, tenant_id, group_id, server_id):
    d = Server.get_by_server_id(client, server_id)

    def serialize(server):
        json_object = {
            'entityId': server.entity_id,
            'groupId': server.group_id,
            'links': [
                {
                    'href': '{0}'.format(request.URLPath().path),
                    'rel': 'self'
                }
            ],
            'serverId': server.server_id
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers/<string:server_id>', methods=['DELETE'])
def delete_server(request, tenant_id, group_id, server_id):
    d = Server.get_by_server_id(client, server_id)

    def delete_server(server):
        return server.delete()
    d.addCallback(delete_server)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies', methods=['GET'])
def get_policies(request, tenant_id, group_id):
    d = Policy.get_all_by_group_id(client, group_id)

    def serialize(policies):
        result = {'policies': policies}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies', methods=['POST'])
def create_policy(request, tenant_id, group_id):
    content = json.loads(request.content.read())
    alarm_template_id = content.get('alarmTemplateId')
    check_template_id = content.get('checkTemplateId')
    policy_id = content.get('policyId')

    d = Policy.new(client, policy_id, group_id, alarm_template_id, check_template_id)

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplateId': policy.alarm_template_id,
            'checkTemplateId': policy.check_template_id,
            'groupId': policy.group_id,
            'links': [
                {
                    'href': '{0}{1}'.format(request.URLPath().path, policy.policy_id),
                    'rel': 'self'
                }
            ],
            'policyId': policy.policy_id
        }
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(201)
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies/<string:policy_id>', methods=['GET'])
def get_policy(request, tenant_id, group_id, policy_id):
    d = Policy.get_by_policy_id(client, policy_id)

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplateId': policy.alarm_template_id,
            'checkTemplateId': policy.check_template_id,
            'groupId': policy.group_id,
            'links': [
                {
                    'href': '{0}'.format(request.URLPath().path),
                    'rel': 'self'
                }
            ],
            'policyId': policy.policy_id
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies/<string:policy_id>', methods=['DELETE'])
def delete_policy(request, tenant_id, group_id, policy_id):
    d = Policy.get_by_policy_id(client, policy_id)

    def delete(policy):
        return policy.delete()
    d.addCallback(delete)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)
