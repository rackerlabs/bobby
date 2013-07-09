import json
from urlparse import parse_qs

from klein import Klein
from silverberg.client import CQLClient
from twisted.internet import endpoints, reactor

from bobby.models import Group, Server

app = Klein()
client = CQLClient(
    endpoints.clientFromString(
        reactor,
        "tcp:{0}:{1}".format('localhost', 9160)),
    'bobby')


@app.route('/groups')
def groups(request):
    d = Group.all(client)

    def _return_result(result):
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)


@app.route('/servers')
def servers(request):
    d = Server.all(client)

    def _return_result(result):
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)


@app.route('/groups/<string:group_id>', methods=['PUT'])
def group_update(request, group_id):
    params = parse_qs(request.content.read())
    group = Group(group_id, params['webhook'][0], client)
    d = group.save()

    def _return_ok(_):
        request.finish()
    return d.addCallback(lambda _: request.finish())


@app.route('/groups/<string:group_id>', methods=['DELETE'])
def group_delete(request, group_id):
    group = Group(group_id, None, client)
    d = group.delete()

    return d.addCallback(lambda _: request.finish())


@app.route('/groups/<string:group_id>/servers/<string:server_id>', methods=['PUT'])
def group_server_update(request, group_id, server_id):
    server = Server(server_id, group_id, "OK", client)
    d = server.save()

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)


@app.route('/groups/<string:group_id>/servers/<string:server_id>', methods=['DELETE'])
def group_server_delete(request, group_id, server_id):
    server = Server(server_id, group_id, None, client)
    d = server.delete()

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)


@app.route('/groups/<string:group_id>/servers/<string:server_id>/webhook', methods=['POST'])
def group_server_webhook(request, group_id, server_id):
    state = (not request.args.get('state')[0] == 'OK')
    server = Server(server_id, group_id, state, client)
    d = server.update()
    #d = db.query('UPDATE SERVERS SET state="{0}" WHERE id="{1}";'.format(
    #    state, server_id))

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)
