from __future__ import absolute_import, division, print_function, unicode_literals

import requests  # noqa


class ServerApiError(Exception):
    def __init__(self, response):
        # type: (requests.Response) -> None
        self.response = response

        super(ServerApiError, self).__init__(response.content)
