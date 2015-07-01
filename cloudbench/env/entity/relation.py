import inflection

__all__ = ['has_many', 'has_one', 'depends_on_one', 'depends_on_many']

def call_parents(name):
    def func(self, *args, **kwargs):
        return getattr(super(self.__class__, self), name)(*args, **kwargs)

    return func

class Relation(object):
    def __init__(self, klass):
        self.klass = klass 

    def augment_has_many_get(self, attributes, name):
        _get_method = inflection.pluralize(name)

        if 'dependents' not in attributes:
            attributes['dependents'] = set()
        attributes['dependents'].add(_get_method)

        def get(this):
            #TODO: easier way to guess the method that we should call
            # here? e.g., virtual_machine vs. virtual_machines
            name  = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            names = inflection.pluralize(name)
            entities = this.env.config.get(_get_method).iteritems()

            ret = []
            for key, entity in entities:
                if (name in entity.config) and (entity.config[name] == this.name):
                    ret.append(entity)
                elif (names in entity.config) and (this.name in entity.config[names].split(",")):
                    ret.append(entity)
            return ret

        attributes[_get_method] = get
        return _get_method

    def augment_has_one_get(self, attributes, name):
        _get_method = inflection.singularize(name)
        _get_config_method = inflection.pluralize(name)

        if 'dependents' not in attributes:
            attributes['dependents'] = set()
        attributes['dependents'].add(_get_method)

        def get(this):
            name  = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            names = inflection.pluralize(name)
            entities = this.env.config.get(_get_method).iteritems()

            for key, entity in entities:
                if (name in entity.config) and (entity.config[name] == this.name):
                    return entity
                elif (names in entity.config) and (entity.config[names] == this.name):
                    return entity
            return None
        attributes[_get_method] = get
        return _get_method

    def augment_depends_on_one_get(self, attributes, name):
        _get_method = inflection.singularize(name)
        _key = inflection.dasherize(
                inflection.underscore(
                    inflection.singularize(self.klass)))
        _get_config_method = inflection.pluralize(name)

        if 'dependencies' not in attributes:
            attributes['dependencies'] = set()
        attributes['dependencies'].add(_get_method)

        def get(this):
            name = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            if _key not in this.config:
                return None

            return next(val for key, val in
                    this.env.config.get(_get_config_method).iteritems() if
                    (val.name == this.config[_key]))
        attributes[_get_method] = get
        return _get_method

    def augment_depends_on_many_get(self, attributes, name):
        _get_method = inflection.pluralize(name)
        _key = inflection.dasherize(
                inflection.underscore(
                    inflection.pluralize(self.klass)))
        _get_config_method = inflection.pluralize(name)

        if 'dependencies' not in attributes:
            attributes['dependencies'] = set()
        attributes['dependencies'].add(_get_method)

        def get(this):
            name = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            if _key not in this.config:
                return {}

            return [val for key, val in
                    this.env.config.get(_get_config_method).iteritems() if
                    val.name in this.config[_key].split(",")]
        attributes[_get_method] = get
        return _get_method

class has_many(Relation):
    def augment(self, attributes, name):
        _get_method = self.augment_has_many_get(attributes, name)

        _delete = call_parents('delete')
        if 'delete' in attributes:
            _delete = attributes['delete']

        def delete(self):
            for item in getattr(self, _get_method)():
                if not item.deleted():
                    item.delete()
            _delete(self)
        attributes['delete'] = delete

        return {inflection.pluralize(name): []}

class has_one(Relation):
    def augment(self, attributes, name):
        _get_method = self.augment_has_one_get(attributes, name)

        _delete = call_parents('delete')
        if 'delete' in attributes:
            _delete = attributes['delete']
        def delete(self):
            item = getattr(self, _get_method)()
            if item and (not item.deleted()):
                item.delete()
            _delete(self)
        attributes['delete'] = delete

        return {inflection.singularize(name): None}

class depends_on_one(Relation):
    def augment(self, attributes, name):
        _get_method = self.augment_depends_on_one_get(attributes, name)

        _create = call_parents('create')
        if 'create' in attributes:
            _create = attributes['create']
        def create(self):
            item = getattr(self, _get_method)()
            if item and (not item.created()):
                item.create()
            _create(self)
        attributes['create'] = create
        return {inflection.singularize(name): None}

class depends_on_many(Relation):
    def augment(self, attributes, name):
        _get_method = self.augment_depends_on_many_get(attributes, name)

        _create = call_parents('create')
        if 'create' in attributes:
            _create = attributes['create']
        def create(self):
            for item in getattr(self, _get_method)():
                if not item.created():
                    item.create()
            _create(self)
        attributes['create'] = create
        return {inflection.pluralize(name): []}

