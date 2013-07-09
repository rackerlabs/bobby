from twisted.web import server
from twisted.application import service, strports

from bobby.db import SqlitePool
from bobby.views import app


application = service.Application('dammit Bobby')
server = strports.service('tcp:9876', server.Site(app.resource()))

def db_ready(_):
    server.setServiceParent(application)
SqlitePool('bobby.sqlite').create().addCallback(db_ready)
