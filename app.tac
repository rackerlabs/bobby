"""Bobby tac file."""
from silverberg.client import CQLClient
from twisted.web import server
from twisted.application import service, strports
from twisted.internet import endpoints, reactor

from bobby import cass
from bobby.views import app


client = CQLClient(
    endpoints.clientFromString(
        reactor,
        "tcp:{0}:{1}".format('localhost', 9160)),
    'bobby')
cass.set_client(client)

application = service.Application('dammit Bobby')
server = strports.service('tcp:9876', server.Site(app.resource()))

server.setServiceParent(application)
