from __future__ import absolute_import, division, print_function, unicode_literals


class ApiResult(dict):
    """
    Attribute access for keys in an API result structure.
    """
    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError:
            raise AttributeError(key)

        return value


class SubResult(object):
    """
    Property accessor for sub-structures in a result.
    """
    def __init__(self, key, constructor, is_list=False):
        self.key = key
        self.constructor = constructor
        self.is_list = is_list

    def __get__(self, instance, owner):
        if instance is not None:
            if self.is_list:
                value = [
                    self.constructor(result) if (result is not None) else result
                    for result in instance[self.key]
                ]
            else:
                value = instance[self.key]
                if value is not None:
                    value = self.constructor(value)

            instance[self.key] = value
            delattr(instance, self.key)
        else:
            value = self

        return value
