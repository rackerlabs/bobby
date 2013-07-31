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
