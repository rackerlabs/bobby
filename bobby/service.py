from twisted.application import service, strports
from twisted.internet import endpoints, reactor
from twisted.python import usage
from twisted.web import server

from silverberg.client import CQLClient

from bobby import cass
from bobby.views import app


class Options(usage.Options):
    """
    Currently unused.
    """


def setUpCQLClient():
    client = CQLClient(
        endpoints.clientFromString(
            reactor,
            "tcp:{0}:{1}".format('localhost', 9160)),
        'bobby')
    cass.set_client(client)


def makeService(options):
    setUpCQLClient()
    application = service.Application("Dammit, Bobby!")
    services = service.IServiceCollection(application)
    bobbyServer = strports.service('tcp:9876', server.Site(app.resource()))
    bobbyServer.setServiceParent(application)
    return services
