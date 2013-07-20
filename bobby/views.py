"""HTTP REST API endpoints."""
import json

from klein import Klein

from bobby import cass

app = Klein()


@app.route('/<string:tenant_id>/groups', methods=['GET'])
def get_groups(request, tenant_id):
    """Get all groups owned by a given tenant_id.

    :param str tenant_id: A tenant id
    """
    d = cass.get_groups_by_tenant_id(tenant_id)

    def _return_result(groups):
        result = {'groups': groups}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)


@app.route('/<string:tenant_id>/groups', methods=['POST'])
def create_group(request, tenant_id):
    """Create a new group.

    Receive application/json content for new group creation.

    :param str tenant_id: A tenant id
    """
    content = json.loads(request.content.read())
    group_id = content.get('groupId')
    notification = content.get('notification')
    notification_plan = content.get('notificationPlan')

    d = cass.create_group(group_id, tenant_id, notification, notification_plan)

    def _serialize_object(group):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'groupId': group['groupId'],
            'links': [{
                'href': '{0}{1}'.format(request.URLPath().path, group['groupId']),
                'rel': 'self'
            }],
            'notification': group['notification'],
            'notificationPlan': group['notificationPlan'],
            'tenantId': group['tenantId']
        }
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(201)
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(_serialize_object)


@app.route('/<string:tenant_id>/groups/<string:group_id>', methods=['GET'])
def get_group(request, tenant_id, group_id):
    """Get a group.

    :param str tenant_id: A tenant id
    :param str group_id: A group id.
    """
    d = cass.get_group_by_id(group_id)

    def serialize_group(group):
        json_object = {
            'groupId': group['groupId'],
            'links': [{
                'href': '{0}'.format(request.URLPath().path),
                'rel': 'self'
            }],
            'notification': group['notification'],
            'notificationPlan': group['notificationPlan'],
            'tenantId': group['tenantId']
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize_group)


@app.route('/<string:tenant_id>/groups/<string:group_id>', methods=['DELETE'])
def delete_group(request, tenant_id, group_id):
    """Delete a group.

    :param str tenant_id: A tenant id
    :param str group_id: A groud id
    """
    d = cass.delete_group(group_id)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers', methods=['GET'])
def get_servers(request, tenant_id, group_id):
    """Get all servers owned by a given group_id.

    :param str tenant_id: A tenant id.
    :param str group_id: A group id.
    """
    d = cass.get_servers_by_group_id(group_id)

    def serialize(servers):
        result = {'servers': servers}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers', methods=['POST'])
def create_server(request, tenant_id, group_id):
    """Create a new server.

    Receive application/json content for new server creation.

    :param str tenant_id: A tenant id
    :param str group_id: A group id
    """
    content = json.loads(request.content.read())
    server_id = content.get('serverId')
    entity_id = content.get('entityId')
    server_policies = content.get('serverPolicies')

    d = cass.create_server(server_id, entity_id, group_id, server_policies)

    def serialize(server):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'entityId': server['entityId'],
            'groupId': server['groupId'],
            'links': [
                {
                    'href': '{0}{1}'.format(request.URLPath().path, server['serverId']),
                    'rel': 'self'
                }
            ],
            'serverId': server['serverId']
        }

        d = cass.get_serverpolicies_for_server(server['serverId'])

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
    """Get a server.

    :param str tenant_id: A tenant id
    :param str group_id: A group id
    :param str server_id: A server id
    """
    d = cass.get_server_by_server_id(server_id)

    def serialize(server):
        json_object = {
            'entityId': server['entityId'],
            'groupId': server['groupId'],
            'links': [
                {
                    'href': '{0}'.format(request.URLPath().path),
                    'rel': 'self'
                }
            ],
            'serverId': server['serverId']
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers/<string:server_id>', methods=['DELETE'])
def delete_server(request, tenant_id, group_id, server_id):
    """Delete a server.

    :param str tenant_id: A tenant id
    :param str group_id: A groud id
    :param str server_id: A server id
    """
    d = cass.delete_server(server_id)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies', methods=['GET'])
def get_policies(request, tenant_id, group_id):
    """Get all policies owned by a given group_id.

    :param str tenant_id: A tenant id.
    :param str group_id: A group id.
    """
    d = cass.get_policies_by_group_id(group_id)

    def serialize(policies):
        result = {'policies': policies}
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies', methods=['POST'])
def create_policy(request, tenant_id, group_id):
    """Create a new policy.

    Receive application/json content for new policy creation.

    :param str tenant_id: A tenant id
    :param str group_id: A group id
    """
    content = json.loads(request.content.read())
    alarm_template_id = content.get('alarmTemplateId')
    check_template_id = content.get('checkTemplateId')
    policy_id = content.get('policyId')

    d = cass.create_policy(policy_id, group_id, alarm_template_id, check_template_id)

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplateId': policy['alarmTemplateId'],
            'checkTemplateId': policy['checkTemplateId'],
            'groupId': policy['groupId'],
            'links': [
                {
                    'href': '{0}{1}'.format(request.URLPath().path, policy['policyId']),
                    'rel': 'self'
                }
            ],
            'policyId': policy['policyId']
        }
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(201)
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies/<string:policy_id>', methods=['GET'])
def get_policy(request, tenant_id, group_id, policy_id):
    """Get a policy.

    :param str tenant_id: A tenant id
    :param str group_id: A group id
    :param str policy_id: A policy id
    """
    d = cass.get_policy_by_policy_id(policy_id)

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplateId': policy['alarmTemplateId'],
            'checkTemplateId': policy['checkTemplateId'],
            'groupId': policy['groupId'],
            'links': [
                {
                    'href': '{0}'.format(request.URLPath().path),
                    'rel': 'self'
                }
            ],
            'policyId': policy['policyId']
        }
        request.setHeader('Content-Type', 'application/json')
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/policies/<string:policy_id>',
           methods=['DELETE'])
def delete_policy(request, tenant_id, group_id, policy_id):
    """Delete a policy.

    :param str tenant_id: A tenant id
    :param str group_id: A groud id
    :param str policy_id: A policy id
    """
    d = cass.delete_policy(policy_id)

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)
