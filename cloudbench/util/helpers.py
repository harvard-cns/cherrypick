import threading

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

