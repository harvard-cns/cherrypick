import unittest
from mock import Mock

from cloudbench.executor import *


class A(object):
    pass

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.ex = Executor(None)
        self.a = map(lambda x: A(), xrange(5))
        self.run_job = Mock()

    def test_job_submission(self):
        j1 = self.ex.submit(self.a[1:3], self.run_job)
        j2 = self.ex.submit(self.a[0:1], self.run_job)

        # self.assertEqual(self.ex.runnable_jobs(), set([j1, j2]))
        # self.ex.run_next_job().join()
        # self.assertEqual(self.run_job.call_count, 1)

        # self.assertEqual(len(self.ex.runnable_jobs()), 1)
        # self.ex.run_next_job().join()
        # self.assertEqual(len(self.ex.runnable_jobs()), 0)

    def test_conflicting_jobs(self):
        j1 = self.ex.submit(self.a[1:3], self.run_job)
        j2 = self.ex.submit(self.a[2:4], self.run_job)

        self.assertEqual(self.ex.runnable_jobs(), set([j1, j2]))

        self.ex.mark_job_as_active(j1)
        self.assertEqual(len(self.ex.runnable_jobs()), 0)
        self.ex.mark_job_as_inactive(j1)
        self.assertEqual(len(self.ex.runnable_jobs()), 2)

    def test_running_jobs(self):
        import time
        mock_func = Mock()
        def timeout_job(*args, **kwargs):
            mock_func(*args, **kwargs)
            #time.sleep(1)

        self.ex.submit(self.a[1:3], timeout_job)
        self.ex.submit(self.a[2:], timeout_job)
        self.ex.submit(self.a[0:3], timeout_job)
        self.ex.submit(self.a[1:4], timeout_job)
        self.ex.submit(self.a[0:1], timeout_job)
        self.ex.submit(self.a[1:2], timeout_job)
        self.ex.submit(self.a[2:3], timeout_job)
        self.ex.submit(self.a[3:4], timeout_job)

        # Because of dependencies, execution should take around 5 seconds
        t = time.time()
        self.ex.run()
        self.assertTrue((time.time() - t) < 6)
        # Mock function should have been called 8 times
        self.assertEqual(mock_func.call_count, 8)

        # Nothing to execute here, should be immediate
        t = time.time()
        self.ex.run()
        self.assertTrue((time.time() - t) < 1)

        # Mock function should have been called 0 times since last call
        self.assertEqual(mock_func.call_count, 8)

