from __future__ import absolute_import, division, print_function, unicode_literals


class ServerApiError(Exception):
    def __init__(self, response):
        self.response = response

        super(ServerApiError, self).__init__(response.content)
