class ApiResult(dict):
    """
    Attribute access for keys in an API result structure.
    """
    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError:
            raise AttributeError(key)
        else:
            value = self._upgrade(value)

        return value

    @staticmethod
    def _upgrade(value):
        if isinstance(value, dict):
            value = ApiResult(value)
        elif isinstance(value, list):
            value = [ApiResult._upgrade(item) for item in value]

        return value
