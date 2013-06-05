import json
from urlparse import parse_qs

from klein import Klein

from bobby.db import SqlitePool

app = Klein()
db = SqlitePool('bobby.sqlite')


@app.route('/groups')
def groups(request):
    d = db.query('SELECT group_id, webhook FROM GROUPS;')

    def _return_result(result):
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)

@app.route('/servers')
def servers(request):
    d = db.query('SELECT id, group_id, state FROM SERVERS;')

    def _return_result(result):
        request.write(json.dumps(result))
        request.finish()
    return d.addCallback(_return_result)

@app.route('/groups/<string:group_id>', methods=['PUT'])
def group_update(request, group_id):
    params = parse_qs(request.content.read())
    d = db.query(
        'INSERT INTO GROUPS ("group_id", "webhook") VALUES ("{0}","{1}");'.format(
            group_id, params['webhook'][0]))

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)

@app.route('/groups/<string:group_id>', methods=['DELETE'])
def group_delete(request, group_id):
    d = db.query('DELETE FROM GROUPS WHERE group_id = {0};'.format(group_id))

    def _return_ok(_):
        request.finish();
    return d.addCallback(_return_ok)

@app.route('/groups/<string:group_id>/servers/<string:server_id>', methods=['PUT'])
def group_server_update(request, group_id, server_id):
    d = db.query('INSERT INTO SERVERS ("id", "group_id", "state") VALUES ("{0}", "{1}", "0");'.format(server_id, group_id))

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)

@app.route('/groups/<string:group_id>/servers/<string:server_id>', methods=['DELETE'])
def group_server_delete(request, group_id, server_id):
    d = db.query('DELETE FROM SERVERS WHERE id = {0};'.format(server_id))

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)

@app.route('/groups/<string:group_id>/servers/<string:server_id>/webhook', methods=['POST'])
def group_server_webhook(request, group_id, server_id):
    state = (not request.args.get('state')[0] == 'OK')
    d = db.query('UPDATE SERVERS SET state="{0}" WHERE id="{1}"'.format(
        state, server_id))

    def _return_ok(_):
        request.finish()
    return d.addCallback(_return_ok)
