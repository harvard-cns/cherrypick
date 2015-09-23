import inflection

from cloudbench.env.entity import *

class EnvConfig(object):
    def __init__(self, f, cloud, env):
        self._env = env
        self._file = f
        self._cloud = cloud
        self._config = {}
        self._entities = {}

    @property
    def env(self):
        return self._env

    def __getattr__(self, name):
        """ Create extend_[name], add_[name], and [name] methods on the
        fly for accessing and extending entities """

        def create_add(var):
            """ Create add entitiy """

            variable = inflection.pluralize(var)
            def add(name, options):
                """ Add entity, save the entity in the entities
                dictionary """

                klass_name = inflection.camelize(var)
                klass = globals()[klass_name]
                if not variable in self._entities:
                    self._entities[variable] = {}
                self._entities[variable][name] = klass(name, options,
                        self.env)
                return self 
            setattr(self, 'add_' + name, add)
            return add

        def create_extend(var):
            """ Create extend entity """
            variable = inflection.pluralize(var)
            def extend(name, options):
                self._entities[variable][name].extend(options)
                return self
            setattr(self, 'extend_' + name, extend)
            return extend

        def create_get(var):
            """ Return the set of all entities with a specific type """
            variable = inflection.pluralize(var)
            def get():
                return self._entities[variable]
            setattr(self, name, get)
            return get

        if name.startswith('extend_'):
            return create_extend(name[7:])
        elif name.startswith('add_'):
            return create_add(name[4:])
        else:
            return create_get(name)

    def get(self, _type, _name=None):
        """ Returns an entity with specific name and type """
        if _type not in self._entities:
            if _name is not None:
                return None
            return {}

        if _name is None:
            return self._entities[_type]
        
        if _name not in self._entities[_type]:
            return None

        return self._entities[_type][_name]

    @property
    def cloud(self):
        return self._cloud

    def parse(self):
        raise Exception("parse method of %s is not defined." %
                self.__class__)

    def config(self, name, value=None):
        if value == None:
            return self._config[name]

        self._config[name] = value
        return value

    def value(self, value):
        if str(value).startswith('config:'):
            return self.config(value[7:])

        if str(value).startswith('global:'):
            return self.env.param(value[7:])

        return value

    def entities(self):
        return self._entities
