"""Tests for bobby.worker."""

from twisted.trial import unittest

from bobby import ele


class TestEleApi(unittest.TestCase):
    """ Test ELE API calls """

    def test_add_check(self):
        """ Test add_check """
        ele.add_check('t1', 'p1', 'en1', {})

    def test_add_alarm(self):
        """ Test add_alarm """
        ele.add_alarm('t1', 'p1', 'en1', 'ch1', 'ALARM DSL', 'np')

    def test_add_notification(self):
        """ Test add_notification """
        ele.add_notification('t1')

    def test_add_notification_plan(self):
        """ Test add_notification_plan """
        ele.add_notification_plan('t1', 'nt')

    def test_fetch_entity_by_uuid(self):
        """ Test fetch_entity_by_uuid """
        ele.fetch_entity_by_uuid('t1', 'p1', 's1')


class TestMaasClient(unittest.TestCase):
    """Test bobby.ele.MaasClient."""

    def test_init(self):
        public_url = u'https://monitoring.api.rackspacecloud.com/v1.0/123'
        auth_token = u'auth-abcdef'
        service_catalog = [
            {u'endpoints': [{
                u'publicURL': public_url,
                u'tenantId': u'675646'}],
             u'name': u'cloudMonitoring',
             u'type': u'rax:monitor'}]
        client = ele.MaasClient(service_catalog, auth_token)

        self.assertEqual(public_url, client._endpoint)
        self.assertEqual(auth_token, auth_token)
