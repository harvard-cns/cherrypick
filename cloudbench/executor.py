from cloudbench.util import parallel

from threading import RLock, Thread
import time

class Job(object):
    def __init__(self, env, entities, function):
        self._entities = entities
        self._function = function
        self._env = env

    @property
    def entities(self):
        return self._entities

    @property
    def env(self):
        return self._env

    def run(self, callback=None):
        def run(self, callback):
            self._function(self._entities, self.env)
            if callback:
                callback(self)
        th = Thread(target=run, args=(self, callback))
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
        return self._remaining_jobs - self.jobs_of(self.active_entities())

    def next_runnable_job(self):
        jobs = self.runnable_jobs()
        if not jobs:
            return None
        return jobs.pop()

    def submit(self, entities, function):
        """ Submit a job for execution """
        job = Job(self._env, entities, function)

        # Add the entities to the set of total entities
        self._entities = self._entities.union(set(entities))
        self._jobs.add(job)
        self._remaining_jobs.add(job)

        # Attach the job to an entity
        for entity in entities:
            if entity not in self._entity_jobs:
                self._entity_jobs[entity] = set()
            self._entity_jobs[entity] = self._entity_jobs[entity].union(set([job]))

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
            if (not hasattr(entity, 'started')) or entity.started():
                return True

            entity.start()

            # Wait 5 times for the instance to come up
            for i in xrange(7):
                if entity.started():
                    return True
                time.sleep(15)
            
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
            self._active_jobs.remove(job)


    def run_next_job(self):
        """ Run next available job """
        job = self.next_runnable_job()

        if not job:
            return False

        if self.start_entities(job.entities):
            self.mark_job_as_active(job)
            self._remaining_jobs.remove(job)
            return job.run(callback=self.mark_job_as_inactive)

        return True

    def finished(self):
        return len(self._remaining_jobs) == 0

    def stop(self):
        def stop_entity(entity):
            if hasattr(entity, 'stop'):
                entity.stop()
            return True
        parallel(stop_entity, self._entities)

    def __call__(self, entities, function):
        self.submit(entities, function)

    def run(self):
        """ Run all the jobs """
        threads = set()
        while not self.finished():
            th = self.run_next_job()
            if isinstance(th, Thread):
                threads.add(th)
                continue

            # If running failed, but we should continue snooping for
            # more jobs
            if th == True:
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
