import requests  # noqa


class ServerApiError(Exception):
    def __init__(self, response):
        # type: (requests.Response) -> None
        self.response = response

        super().__init__(response.content)
