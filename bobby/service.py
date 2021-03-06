from twisted.application import service, strports
from twisted.internet import endpoints, reactor
from twisted.python import usage
from twisted.web import server

from silverberg.client import CQLClient

from bobby.views import Bobby


class Options(usage.Options):
    """
    """
    optParameters = [
        ["port", "p", 9876,
         "The bobby port for API connections."],
        ["cql-host", "h", "localhost",
         "The CQL host for client communications."],
        ["cql-port", "c", 9160,
         "The CQL port for client communications."]]


def makeService(options):
    cql_client = CQLClient(
        endpoints.clientFromString(
            reactor,
            "tcp:{0}:{1}".format(options["cql-host"], options["cql-port"])),
        'bobby')
    application = service.Application("Dammit, Bobby!")
    services = service.IServiceCollection(application)
    bobby = Bobby(cql_client)
    bobbyServer = strports.service(
        'tcp:{0}'.format(options["port"]),
        server.Site(bobby.app.resource()))
    bobbyServer.setServiceParent(application)
    return services
