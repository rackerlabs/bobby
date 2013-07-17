import json

from klein import Klein
from silverberg.client import CQLClient
from twisted.internet import endpoints, reactor

from bobby.models import Group

app = Klein()
client = CQLClient(
    endpoints.clientFromString(
        reactor,
        "tcp:{0}:{1}".format('localhost', 9160)),
    'bobby')


@app.route('/<string:tenant_id>/groups', methods=['GET'])
def get_groups(request, tenant_id):
    d = Group.get_by_tenant_id(tenant_id)

    def _return_result(groups):
        result = {'groups': groups}
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)


@app.route('/<string:tenant_id>/groups', methods=['PUT'])
def create_group(request, tenant_id):
    group_id = request.args.get('groupId')[0]
    group_webhook = request.args.get('webhook')[0]

    d = Group.new(group_id, group_webhook)

    def _serialize_object(group):
        # XXX: the actual way to do this is using a json encoder. Not now.
        json_object = {
            'groupId': group.group_id,
            'links': {
                'href': '{0}{1}'.format(request.postpath, group.group_id),
                'rel': 'self'
            },
            'webhook': group.webhook
        }

        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(_serialize_object)


@app.route('/<string:tenant_id>/groups/{group_id}', methods=['GET'])
def get_group(request, tenant_id, group_id):
    d = Group.get_by_group_id(tenant_id, group_id)

    def serialize_group(group):
        json_object = {
            'groupId': group.group_id,
            'links': [
                {
                    'href': '{0}'.format(request.postpath),
                    'rel': 'self'
                }
            ],
            'webhook': group.webhook
        }
        request.write(json.dumps(json_object))
        request.finish()
    return d.addCallback(serialize_group)


@app.route('/<string:tenant_id>/groups/{group_id}', methods=['DELETE'])
def delete_group(request, tenant_id, group_id):
    d = Group.get_by_group_id()

    def delete_group(group):
        return group.delete()
    d.addCallback(delete_group)

    def finish(_):
        request.setResponseCode(204)
        request.finish()
    return d.addCallback(finish)
