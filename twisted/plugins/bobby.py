from twisted.application.service import ServiceMaker


bobbyService = ServiceMaker(
    "Bobby Service/",
    "bobby.service",
    "Monitoring integration for Autoscale.",
    "bobby")
