import inflection

__all__ = ['has_many', 'has_one', 'depends_on_one', 'depends_on_many']

def call_parents(name):
    def func(self, *args, **kwargs):
        return getattr(super(self.__class__, self), name)(*args, **kwargs)
    return func

#   def _silent_remove(self, other):
#       var_name = other._variable(self)
#       var = getattr(other, var_name)
#
#       if isinstance(var, list):
#           var.remove(self)
#       else:
#           if var == self:
#               setattr(other, var_name, None)
#
#   def _silent_add(self, other):
#       var_name = other._variable(self)
#       var = getattr(other, var_name)
#
#       if isinstance(var, list):
#           if self not in var:
#               var.append(self)
#       else:
#           setattr(other, var_name, self)

class Relation(object):
    def __init__(self, klass):
        self.klass = klass 

    def verify_class(self, obj):
        return (obj.__class__.__name__ == self.klass)

    def augment_has_many_get(self, attributes, name):
        _get_method = inflection.pluralize(name)
        def get(this):
            #TODO: easier way to guess the method that we should call
            # here? e.g., virtual_machine vs. virtual_machines
            name  = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            names = inflection.pluralize(name)
            entities = this.env.config().get(_get_method).iteritems()

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
        def get(this):
            name  = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            names = inflection.pluralize(name)
            entities = this.env.config().get(_get_method).iteritems()

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
        _key = inflection.dasherize(_get_method)
        _get_config_method = inflection.pluralize(name)
        def get(this):
            name = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            if _key not in this.config:
                return None

            return next(val for key, val in
                    this.env.config().get(_get_config_method).iteritems() if
                    (val.name == this.config[_key]))
        attributes[_get_method] = get
        return _get_method

    def augment_depends_on_many_get(self, attributes, name):
        _get_method = inflection.pluralize(name)
        _key = inflection.dasherize(_get_method)
        _get_config_method = inflection.pluralize(name)
        def get(this):
            name = inflection.dasherize(inflection.underscore(this.__class__.__name__))
            if _key not in this.config:
                return {}

            return [val for key, val in
                    this.env.config().get(_get_config_method).iteritems() if
                    val.name in this.config[_key].split(",")]
        attributes[_get_method] = get
        return _get_method


#   def augment_auto_get(self, attributes, name):
#       _get_method = inflection.pluralize(name)
#       def get(this):
#           return this.config().get(_get_method).values()
#       attributes[_get_method] = get
#       return _get_method
#
#   def augment_array_get(self, attributes, name):
#       """ Add pluralize(name) method to the class """
#       variable = '_' + inflection.pluralize(name)
#       _get_method = inflection.pluralize(name)
#       def get(this):
#           return getattr(this, variable)
#       attributes[_get_method] = get
#       return _get_method
#
#   def augment_get(self, attributes, name):
#       """ Add singularize(name) method to the class """
#       variable = '_' + inflection.singularize(name)
#       _get_method = inflection.singularize(name)
#       def get(this):
#           return getattr(this, variable)
#       attributes[_get_method] = get
#       return _get_method
#
#   def augment_find(self, attributes, name):
#       """ Add singularize(name)(name_to_find) method to the class """
#       variable = '_' + inflection.pluralize(name)
#       _find_method = inflection.singularize(name)
#       def find(this, what):
#           items = getattr(this, variable)
#           return next(item for item in items if item.name == what)
#       attributes[_find_method] = find
#       return _find_method
#
#   def augment_remove(self, attributes, name):
#       """ Remove other from pluralize(name) """
#       variable = '_' + inflection.pluralize(name)
#       _remove_method = 'remove_' + inflection.singularize(name)
#       def remove(this, other):
#           _silent_remove(this, other)
#           getattr(this, variable).remove(other)
#           return this
#       attributes[_remove_method] = remove
#       return _remove_method
#
#   def augment_add(self, attributes, name):
#       """ Add other to pluralize(name) """
#       variable = '_' + inflection.pluralize(name)
#       _add_method = 'add_' + inflection.singularize(name)
#       def add(this, other):
#           if not self.verify_class(other):
#               raise TypeError("'%s' should be an instance of '%s'" %
#                       (other, self.klass))
#           _silent_add(this, other)
#           getattr(this, variable).append(other)
#           return this 
#       attributes[_add_method] = add
#       return _add_method
#
#   def augment_set(self, attributes, name):
#       """ Remove or add other to singularize(name) """
#       variable = '_' + inflection.singularize(name)
#       _set_method = 'set_' + inflection.singularize(name)
#       def set_(this, other):
#           if not self.verify_class(other):
#               raise TypeError("'%s' should be an instance of '%s'" %
#                       (other, self.klass))
#           if other is not None:
#               _silent_add(this, other)
#           else:
#               _silent_remove(this, other)
#           setattr(this, variable, other)
#           return this
#       attributes[_set_method] = set_
#       return _set_method


class has_many(Relation):
    def augment(self, attributes, name):
        # _get_method = self.augment_array_get(attributes, name)
        # self.augment_find(attributes, name)
        # self.augment_add(attributes, name)
        # self.augment_remove(attributes, name)
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
        # self.augment_set(attributes, name)
        # _get_method = self.augment_get(attributes, name)
        _get_method = self.augment_has_one_get(attributes, name)

        _delete = call_parents('delete')
        if 'delete' in attributes:
            _delete = attributes['delete']
        def delete(self):
            item = getattr(self, _get_method)
            if item and (not item.deleted()):
                item.delete()
            _delete(self)
        attributes['delete'] = delete

        return {inflection.singularize(name): None}

class depends_on_one(Relation):
    def augment(self, attributes, name):
        # self.augment_set(attributes, name)
        # _get_method = self.augment_get(attributes, name)
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
        #_get_method = self.augment_array_get(attributes, name)
        #self.augment_find(attributes, name)
        #self.augment_add(attributes, name)
        #self.augment_remove(attributes, name)
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

