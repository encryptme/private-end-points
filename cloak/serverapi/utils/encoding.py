import six
from typing import Any  # noqa


def force_text(value, encoding='utf-8'):
    # type: (Any, str) -> str
    """ Returns value as a unicode string. """
    if isinstance(value, six.text_type):
        pass
    elif isinstance(value, six.binary_type):
        value = value.decode(encoding)
    else:
        value = six.text_type(value)

    return value
