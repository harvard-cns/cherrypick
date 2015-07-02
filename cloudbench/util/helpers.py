import threading
import time

def parallel(action, lst):
    """ Run an action in parallel and wait for completion """
    threads = []
    for item in lst:
        thread = threading.Thread(target=action, args=(item,))
        threads.append(thread)
        thread.daemon = True
        thread.start()

    for thread in threads:
        thread.join()

def entity_repr(entity, _type):
    """ Returns the representation of an entity """
    ret = "%s(%s):\n" % (_type, entity.name)
    for key, val in entity.config().iteritems():
        ret += "   > %s: %s\n" % (key, val)
    return ret

def rate_limit(speed):
    interval = 1/float(speed)

    def decorate(f):
        last_time = [time.time()]
        lock = [threading.RLock()]

        def func(*args, **kwargs):
            with lock[0]:
                remaining = time.time() - (last_time[0] + interval)
                if remaining < 0:
                    time.sleep(-remaining)

                last_time[0] = time.time()
            return f(*args, **kwargs)
        return func
    return decorate
