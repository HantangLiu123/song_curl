import requests

class RequestsGet:

    """a class for the get requests

    a class that stores headers and cookies for 
    get requests
    """

    def __init__(self, headers: dict[str, str], cookies: dict[str, str]):
        self.headers = headers
        self.cookies = cookies

    def requests_get(self, url: str, params: dict):
        return requests.get(url, headers=self.headers, cookies=self.cookies, params=params)