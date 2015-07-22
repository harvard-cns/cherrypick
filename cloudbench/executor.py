from cloudbench.util import parallel
from cloudbench.env.entity.behavior import Preemptable

from threading import RLock, Thread
import time

glob_lock = RLock()
glob_job = {}

class Job(object):
    count = 0
    def __init__(self, env, entities, function, name=''):
        self.count = Job.count
        with glob_lock:
            Job.count += 1
        self._entities = entities
        self._function = function
        self._name = name
        self._env = env


    def __repr__(self):
        return str(self.count)

    @property
    def entities(self):
        return self._entities

    @property
    def env(self):
        return self._env

    def run(self, callback=None):
        def execute(job, callback):
            self._function(job._entities, job.env)
            if callback:
                callback(job)
        th = Thread(target=execute, args=(self, callback))
        th.daemon = True
        th.start()

        return th

class Executor(object):
    def __init__(self, env):
        self._env = env

        self._entities = set()

        self._jobs = set()
        self._remaining_jobs = set()
        self._active_jobs = set()
        self._entity_jobs = {}

        self._dead_entities = set()

        self._active_job_lock = RLock()
        self._remaining_job_lock = RLock()


    @property
    def env(self):
        return self._env

    
    def jobs_of(self, entities):
        ret = set()
        for entity in entities:
            ret = ret.union(self._entity_jobs[entity])

        return ret

    def runnable_jobs(self):
        """ Returns the set of jobs that can be run """
        # Returns the set of runnable jobs
        with self._remaining_job_lock:
            return self._remaining_jobs - self.jobs_of(self.active_entities())

    def next_runnable_job(self):
        with self._remaining_job_lock:
            jobs = self.runnable_jobs()
            if not jobs:
                return None
            job = jobs.pop()
            self._remaining_jobs.remove(job)
            return job

    def submit(self, entities, function, name=''):
        """ Submit a job for execution """
        job = Job(self._env, entities, function, name)

        # Add the entities to the set of total entities
        self._entities = self._entities.union(set(entities))
        self._jobs.add(job)
        self._remaining_jobs.add(job)

        # Attach the job to an entity
        for entity in entities:
            if entity not in self._entity_jobs:
                self._entity_jobs[entity] = set()
            self._entity_jobs[entity].add(job)

        return job


    def add_dead_entities(self, entities):
        """ Add dead entities """
        self._dead_entities = self._dead_entities.union(entities)

        # Remove the rest of the jobs that can't be run
        self._remaining_jobs = self._remaining_jobs - self.jobs_of(entities)

    def start_entities(self, entities):
        """ Start the entities for a job """
        dead_entities = set()
        lock = RLock()

        def entity_up(entity):
            if not isinstance(entity, Preemptable):
                return True

            entity.start()
            entity.wait(180)

            if entity.stale:
                with lock:
                    dead_entities.add(entity)

        parallel(entity_up, entities)

        if len(dead_entities) > 0:
            self.add_dead_entities(dead_entities)
            return False

        return True

    def active_entities(self):
        """ Return the set of active entities """
        ret = set()
        with self._active_job_lock:
            for job in self._active_jobs:
                ret = ret.union(job.entities)

        return ret

    def mark_job_as_active(self, job):
        with self._active_job_lock:
            self._active_jobs.add(job)

    def mark_job_as_inactive(self, job):
        with self._active_job_lock:
            self._active_jobs.discard(job)

    def add_remaining(self, job):
        with self._remaining_job_lock:
            self._remaining_jobs.add(job)

    def run_next_job(self):
        """ Run next available job """
        job = self.next_runnable_job()
        if not job:
            return False

        def run_job(job):
            self.mark_job_as_active(job)
            if not self.start_entities(job.entities):
                self.mark_job_as_inactive(job)
                return True

            th = job.run(callback=self.mark_job_as_inactive)
            th.join()

        th = Thread(target=run_job, args=(job,))
        th.daemon = True
        th.start()
        return th

    def finished(self):
        return len(self._remaining_jobs) == 0

    def stop(self):
        def stop_entity(entity):
            if hasattr(entity, 'stop'):
                entity.stop()
            return True
        parallel(stop_entity, self._entities)

    def __call__(self, entities, function, name=''):
        self.submit(entities, function, name)

    def save_dead_entities(self):
        for entity in self._dead_entities:
            self.env.storage().save({'stale': entity.name}, partition='dead')

    def run(self):
        """ Run all the jobs """
        threads = set()
        while not self.finished():
            th = self.run_next_job()
            if isinstance(th, Thread):
                threads.add(th)
                continue

            # If th is none, that means there are no jobs for us to
            # execute, do a busy loop until at least one of the threads
            # are free for execution
            loop = True
            while loop:
                for thread in threads:
                    thread.join(0.1)
                    if not thread.isAlive():
                        threads.remove(thread)
                        loop = False
                        break

        for thread in threads:
            thread.join()

        # Save the dead entities
        self.save_dead_entities()
