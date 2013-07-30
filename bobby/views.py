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
    d = cass.get_group_by_id(tenant_id, group_id)

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
    d = cass.delete_group(tenant_id, group_id)

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
    d = cass.get_servers_by_group_id(tenant_id, group_id)

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

    d = cass.create_server(tenant_id, server_id, entity_id, group_id)

    # Trigger actions to actually create the server's monitoring here

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

        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(201)
        request.write(json.dumps(json_object))
        request.finish()

    return d.addCallback(serialize)


@app.route('/<string:tenant_id>/groups/<string:group_id>/servers/<string:server_id>', methods=['GET'])
def get_server(request, tenant_id, group_id, server_id):
    """Get a server.

    :param str tenant_id: A tenant id
    :param str group_id: A group id
    :param str server_id: A server id
    """
    d = cass.get_server_by_server_id(tenant_id, server_id)

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
    d = cass.delete_server(tenant_id, server_id)

    # Trigger actions to remove the MaaS Checks and alarms and stuff in an orderly fashion
    # here...

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
    alarm_template_id = content.get('alarmTemplate')
    check_template_id = content.get('checkTemplate')
    policy_id = content.get('policyId')

    d = cass.create_policy(policy_id, group_id, alarm_template_id, check_template_id)

    # Trigger actions to create the alarm and checks on the MaaS side and set things up

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplate': policy['alarmTemplate'],
            'checkTemplate': policy['checkTemplate'],
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
    d = cass.get_policy_by_policy_id(group_id, policy_id)

    def serialize(policy):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'alarmTemplate': policy['alarmTemplate'],
            'checkTemplate': policy['checkTemplate'],
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

    # Trigger actions to remove the MaaS Checks and alarms and stuff in an orderly fashion
    # here...

    def finish(_):
        request.setHeader('Content-Type', 'application/json')
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)


@app.route('/alarm', methods=['POST'])
def alarm(request):
    """Change the state of an alarm."""
    content = json.loads(request.content.read())
    alarm_id = content.get('alarm').get('id')
    status = content.get('details').get('state')

    d = cass.alter_alarm_state(alarm_id, status)

    def check_quorum_health(results):
        policy_id, server_id = results
        return cass.check_quorum_health(policy_id)
    d.addCallback(check_quorum_health)

    def finish(health):
        #TODO: do something with server health

        request.setResponseCode(200)
        request.finish()
    return d.addCallback(finish)
