import unittest
from mock import Mock
import sys

from cloudbench.env.entity.behavior import *
from cloudbench.env.clouds import AzureCloud
from cloudbench.ssh import Ssh

class TestSecureShell(unittest.TestCase):
    """ Test secure shell behaviour """
    class VirtualMachine(SecureShell):
        def __init__(self):
            self.username = 'testing'
            self.url = 'localhost'
            super(self.__class__, self).__init__()

    def setUp(self):
        self.vm = self.__class__.VirtualMachine()

    def test_ssh(self):
        self.assertIsInstance(self.vm.ssh(False, False), Ssh)
        self.assertEqual(self.vm.ssh(False, False), self.vm.ssh(False, False))

    def test_new_ssh(self):
        self.assertNotEqual(self.vm.ssh(False, False), self.vm.ssh(True, False))
        self.assertNotEqual(self.vm.ssh(True, False), self.vm.ssh(True, False))

class TestPreemptable(unittest.TestCase):
    """ Test a preemptable object behavior """
    class VirtualMachine(Preemptable):
        def __init__(self):
            super(self.__class__, self).__init__()
            self.factory = m = Mock(spec=AzureCloud)

    def setUp(self):
        self.m = self.__class__.VirtualMachine()
        self.f = self.m.factory

    def test_function_calls(self):
        # Make sure the functions are called once initially, when the
        # virtual_machine is in unknown state
        self.m.started()
        self.m.stopped()

        self.f.status_virtual_machine.assert_called_once_with(self.m)
        self.f.status_virtual_machine.assert_called_once_with(self.m)

    def test_start_a_stopped_object(self):
        # If an object is stopped and is started, it should call the
        # start method once.
        self.f.status_virtual_machine.return_value = False
        self.assertFalse(self.m.started())
        self.m.start()
        self.f.start_virtual_machine.assert_called_once(self.m)

    def test_stop_a_started_object(self):
        self.f.status_virtual_machine.return_value = True
        self.assertTrue(self.m.started())
        self.m.stop()
        self.f.stop_virtual_machine.assert_called_once_with(self.m)

    def test_started_should_call_factory_once(self):
        # After we start, when started() is called, we should verify
        # once more time to make sure that entity has started
        self.f.reset_mock()
        self.f.status_virtual_machine.return_value = True
        self.assertTrue(self.m.started())
        self.f.status_virtual_machine.assert_called_once_with(self.m)

        # Subsequent calls to "status_", shouldn't query the start
        # method of the factory since once the object has started, we
        # don't need to query it anymore -- we should cache the
        # successful result
        self.f.reset_mock()
        self.m.started()
        self.assertEqual(self.f.status_virtual_machine.call_count, 0)

    def test_start_or_stop_should_make_status_unknown(self):
        # When we stop the machine, we should be in unknown state
        # Until we verify it with started or stopped
        self.f.status_virtual_machine.return_value = None

        self.m.stop()
        self.assertEqual(self.m._started, None)

        self.m.start()
        self.assertEqual(self.m._started, None)

        # After calling started or stopped we will "hopefully"
        # be in a predictable state
        self.f.reset_mock()
        self.f.status_virtual_machine.return_value = True
        self.m.started()
        self.assertNotEqual(self.m._started, None)
        self.assertEqual(self.f.status_virtual_machine.call_count, 1)

    def test_started_should_cache_results_in_predictable_state(self):
        self.f.status_virtual_machine.return_value = False
        self.m.started()

        # Call only once, cache the result of the last call
        self.m.started()
        self.assertEqual(self.f.status_virtual_machine.call_count, 1)

    def test_stopped_should_cache_results_in_predictable_state(self):
        self.f.status_virtual_machine.return_value = False
        self.m.stopped()

        # Call only once, cache the result of the last call
        self.m.stopped()
        self.assertEqual(self.f.status_virtual_machine.call_count, 1)

    def test_reset(self):
        self.f.status_virtual_machine.return_value = None
        self.m.reset()
        self.f.stop_virtual_machine.assert_called_once_with(self.m)
        self.f.start_virtual_machine.assert_called_once_with(self.m)
