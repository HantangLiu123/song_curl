import requests

class RequestsGet:

    """a class for the get requests

    A class that stores headers and cookies for get requests. This class exists
    since all the requests in the code use the same headers and cookies.

    Attributes:
        headers (dict[str, str]): the headers for the requests
        cookies (dict[str, str]): the cookies for the requests
    """

    def __init__(self, headers: dict[str, str], cookies: dict[str, str]):

        """using the headers and cookies to initialize this request class"""

        self.headers = headers
        self.cookies = cookies

    def requests_get(self, url: str, params: dict | None = None):

        """using the url and params to do the get request
        
        Args:
            url (str): the url of the request
            params (dict | None): the params of the request

        Returns:
            response (Response): the response of the request
        """

        return requests.get(url, headers=self.headers, cookies=self.cookies, params=params)