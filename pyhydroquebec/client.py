"""PyHydroQuebec Client Module."""
import uuid
from datetime import datetime
import random
import string
from json import dumps as json_dumps

import aiohttp

from pyhydroquebec.customer import Customer
from pyhydroquebec.error import PyHydroQuebecHTTPError, PyHydroQuebecError
from pyhydroquebec.consts import (REQUESTS_TIMEOUT, CONTRACT_URL_1, CONTRACT_URL_2,
                                  CONTRACT_URL_3, CONTRACT_CURRENT_URL_1, LOGIN_URL_3,
                                  LOGIN_URL_4, LOGIN_URL_5, LOGIN_URL_6, LOGIN_URL_7)


class HydroQuebecClient():
    """PyHydroQuebec HTTP Client."""

    def __init__(self, username, password, timeout=REQUESTS_TIMEOUT,
                 session=None):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._customers = []
        self._session = session
        self._timeout = timeout
        self.guid = str(uuid.uuid1())
        self.access_token = None
        self.cookies = {}
        self._selected_customer = None

    async def http_request(self, url, method, params=None, data=None,
                           headers=None, ssl=True, cookies=None, status=200):
        """Wrapper function making an HTTP request."""
        site = url.split("/")[2]
        if params is None:
            params = {}
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        if cookies is None:
            if site not in self.cookies:
                self.cookies[site] = {}
            cookies = self.cookies[site]

        raw_res = await getattr(self._session, method)(url,
                params=params,
                data=data,
                allow_redirects=False,
                ssl=ssl,
                cookies=cookies,
                headers=headers)
        if raw_res.status != status:
            raise PyHydroQuebecHTTPError("Error Fetching {}".format(url))

        for cookie, cookie_content in raw_res.cookies.items():
            if hasattr(cookie_content, 'value'):
                self.cookies[site][cookie] = cookie_content.value
            else:
                self.cookies[site][cookie] = cookie_content

        return raw_res

    async def select_customer(self, account_id, customer_id, force=False):
        """Select a customer on the Home page.

        Equivalent to click on the customer box on the Home page.
        """
        if self._selected_customer == customer_id and not force:
            return

        if force and "cl-ec-spring.hydroquebec.com" in self.cookies:
            del self.cookies["cl-ec-spring.hydroquebec.com"]

        customers = [c for c in self._customers if c.customer_id == customer_id]
        if not customers:
            raise PyHydroQuebecError("Customer ID {} not found.".format(customer_id))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.access_token,
            "NO_PARTENAIRE_DEMANDEUR": account_id,
            "NO_PARTENAIRE_TITULAIRE": customer_id,
            "DATE_DERNIERE_VISITE": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
            "GUID_SESSION": self.guid
            }

        await self.http_request(CONTRACT_URL_1, "get", headers=headers)

        params = {"mode": "web"}
        await self.http_request(CONTRACT_URL_2, "get",
                params=params,
                headers=headers)

        # load overview page
        await self.http_request(CONTRACT_URL_3, "get")
        # load consumption profile page
        await self.http_request(CONTRACT_CURRENT_URL_1, "get")

        self._selected_customer = customer_id


    @property
    def selected_customer(self):
        """Return the current selected customer."""
        return self._selected_customer

    def _get_httpsession(self):
        """Set http session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(requote_redirect_url=False,)

    async def login(self):
        """

        Hydroquebec is using ForgeRock solution for authentication.
        """
        # Get http session
        self._get_httpsession()

        # Get the callback template
        headers = {"Content-Type": "application/json",
                   "X-NoSession": "true",
                   "X-Password": "anonymous",
                   "X-Requested-With": "XMLHttpRequest",
                   "X-Username": "anonymous"}
        res = await self.http_request(LOGIN_URL_3, "post", headers=headers)
        data = await res.json()

        # Fill the callback template
        data['callbacks'][0]['input'][0]['value'] = self.username
        data['callbacks'][1]['input'][0]['value'] = self.password

        data = json_dumps(data)

        # TODO catch error
        res = await self.http_request(LOGIN_URL_3, "post", data=data, headers=headers)
        json_res = await res.json()

        if 'tokenId' not in json_res:
            print("Unable to authenticate. You can retry and/or check your credentials.")
            return

        # Find settings for the authorize
        res = await self.http_request(LOGIN_URL_4, "get")

        sec_config = await res.json()
        oauth2_config = sec_config['oauth2'][0]

        client_id = oauth2_config['clientId']
        redirect_uri = oauth2_config['redirectUri']
        scope = oauth2_config['scope']
        # Generate some ramdon strings
        state = "".join(random.choice(string.digits + string.ascii_letters) for i in range(40))
        nonce = state
        # TODO find where this setting comes from
        response_type = "id_token token"

        # Get bearer token
        params = {
                "response_type": response_type,
                "client_id": client_id,
                "state": state,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "nonce": nonce,
                "locale": "en"
                }
        res = await self.http_request(LOGIN_URL_5, "get", params=params, status=302)

        # Go to Callback URL
        callback_url = res.headers['Location']
        await self.http_request(callback_url, "get")

        raw_callback_params = callback_url.split('/callback#', 1)[-1].split("&")
        callback_params = dict([p.split("=", 1) for p in raw_callback_params])

        # Check if we have the access token
        if 'access_token' not in callback_params or not callback_params['access_token']:
            print("Access token not found")
            return

        self.access_token = callback_params['access_token']

        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer " + self.access_token}
        await self.http_request(LOGIN_URL_6, "get", headers=headers)

        ####
        # Get customer

        res = await self.http_request(LOGIN_URL_7, "get", headers=headers)
        json_res = await res.json()

        for account in json_res:
            account_id = account['noPartenaireDemandeur']
            customer_id = account['noPartenaireTitulaire']

            customer = Customer(self, account_id, customer_id, self._timeout)
            self._customers.append(customer)
            await customer.fetch_summary()

    @property
    def customers(self):
        """Return Contract list."""
        return self._customers

    async def close_session(self):
        """Close current session."""
        await self._session.close()
