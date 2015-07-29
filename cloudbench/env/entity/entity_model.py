import inflection

from .relation import Relation
from threading import RLock

import pdb

def call_parents(name):
    def func(self, *args, **kwargs):
        return getattr(super(self.__class__, self), name)(*args, **kwargs)
    return func

class Entity(type):
    _entities = []

    @classmethod
    def entities(cls):
        return cls._entities

    """ The metaclass of an entity.

    1) Augments class with methods for accessing objects that are
    required to be created before this class:
        depends_on, depends_on_many
    2) Augments class with methods for accessing objects that depend on
    this object:
        has_many, has_one
    """
    def __new__(self, cls, parents, attributes):
        if cls != 'EntityModel':
            Entity.entities().append(cls)
        __init__ = call_parents('__init__')
        if '__init__' in attributes:
            __init__ = attributes['__init__']

        variables = {}
        attrs = dict(attributes)

        # Add dependencies and dependents variables
        attributes['dependencies'] = set()
        attributes['dependents'] = set()

        # Augment the class with new properties
        for key, val in attrs.iteritems():
            if isinstance(val, Relation):
                variables.update(val.augment(attributes, key))

        def initialize(self, *args, **kwargs):
            for key, val in variables.iteritems():
                setattr(self, '_' + key, val)

            # Call use initialize method
            __init__(self, *args, **kwargs)

        attributes['__init__'] = initialize
        return super(Entity, self).__new__(self, cls, parents, attributes)

class EntityModel(object):
    __metaclass__ = Entity

    def __init__(self, name = '', config = {}, env = None):
        super(EntityModel, self).__init__()

        self._env = env
        self._name = name
        self._config = config
        self._created = False
        self._deleted = False

        self._delete_mutex = RLock()
        self._create_mutex = RLock()

    def created(self, yes=None):
        if yes is not None:
            self._created = yes
        return self._created

    def create(self):
        self._create_mutex.acquire()
        if self.created():
            return True

        ret = self.invoke_action('create')
        self.created(ret)
        self._create_mutex.release()
        return ret

    def deleted(self, yes=None):
        if yes is not None:
            self._deleted = yes
        return self._deleted

    def delete(self):
        self._delete_mutex.acquire()
        if self.deleted():
            return True

        ret = self.invoke_action('delete')
        self.deleted(ret)
        self._delete_mutex.release()
        return ret

    def invoke_action(self, method):
        method = method + '_' + inflection.underscore(self.__class__.__name__)
        if hasattr(self.factory, method):
            return getattr(self.factory, method)(self)

        raise AttributeError("'%s' could not be found on '%s'" % (
            method, self.factory.__class__.__name__))

    @property
    def factory(self):
        return self.env.manager

    @property
    def env(self):
        return self._env

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._config

    def extend(self, _config):
        self.config.update(_config)

    def __contains__(self, name):
        name = inflection.dasherize(name)
        return name in self.config

    def __getattr__(self, name):
        name = inflection.dasherize(name)
        if name in self.config:
            return self.config[name]

        raise AttributeError(name)

    def __str__(self):
        return self.name

    def _repr__(self):
        ret = "\n%s(%s):" % (self.__class__.__name__, self.name)
        for key, val in self.config.iteritems():
            ret += "\n   > %s: %s" % (key, val)
        return ret
