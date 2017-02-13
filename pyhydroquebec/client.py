"""
PyHydroQuebec
"""
import json
import logging
import re

from bs4 import BeautifulSoup
import requests

REQUESTS_TIMEOUT = 15

HOST = "https://www.hydroquebec.com"
HOME_URL = "{}/portail/web/clientele/authentification".format(HOST)
PROFILE_URL = ("{}/portail/fr/group/clientele/"
               "portrait-de-consommation".format(HOST))
MONTHLY_MAP = (('period_total_bill', 'montantFacturePeriode'),
               ('period_length', 'nbJourLecturePeriode'),
               ('period_total_days', 'nbJourPrevuPeriode'),
               ('period_mean_daily_bill', 'moyenneDollarsJourPeriode'),
               ('period_mean_daily_consumption', 'moyenneKwhJourPeriode'),
               ('period_total_consumption', 'consoTotalPeriode'),
               ('period_lower_price_consumption', 'consoRegPeriode'),
               ('period_higher_price_consumption', 'consoHautPeriode'))
DAILY_MAP = (('yesterday_total_consumption', 'consoTotalQuot'),
             ('yesterday_lower_price_consumption', 'consoRegQuot'),
             ('yesterday_higher_price_consumption', 'consoHautQuot'))


class PyHydroQuebecError(Exception):
    pass


class HydroQuebecClient(object):

    def __init__(self, username, password, timeout=REQUESTS_TIMEOUT):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._data = {}
        self._cookies = None
        self._timeout = timeout

    def _get_login_page(self):
        """Go to the login page."""
        try:
            raw_res = requests.get(HOME_URL, timeout=REQUESTS_TIMEOUT)
        except OSError:
            raise PyHydroQuebecError("Can not connect to login page")
        # Get cookies
        self._cookies = raw_res.cookies
        # Get login url
        soup = BeautifulSoup(raw_res.content, 'html.parser')
        form_node = soup.find('form', {'name': 'fm'})
        if form_node is None:
            raise PyHydroQuebecError("No login form find")
        login_url = form_node.attrs.get('action')
        if login_url is None:
            raise PyHydroQuebecError("Can not found login url")
        return login_url

    def _post_login_page(self, login_url):
        """Login to HydroQuebec website."""
        data = {"login": self.username,
                "_58_password": self.password}

        try:
            raw_res = requests.post(login_url,
                                    data=data,
                                    cookies=self._cookies,
                                    allow_redirects=False,
                                    timeout=REQUESTS_TIMEOUT)
        except OSError:
            raise PyHydroQuebecError("Can not submit login form")
        if raw_res.status_code != 302:
            raise PyHydroQuebecError("Bad HTTP status code")

        # Update cookies
        self._cookies.update(raw_res.cookies)
        return True

    def _get_p_p_id(self):
        """Get id of consumption profile."""
        from bs4 import BeautifulSoup
        try:
            raw_res = requests.get(PROFILE_URL,
                                   cookies=self._cookies,
                                   timeout=REQUESTS_TIMEOUT)
        except OSError:
            raise PyHydroQuebecError("Can not get profile page")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Looking for p_p_id
        soup = BeautifulSoup(raw_res.content, 'html.parser')
        p_p_id = None
        for node in soup.find_all('span'):
            node_id = node.attrs.get('id', "")
            if node_id.startswith("p_portraitConsommation_WAR"):
                p_p_id = node_id[2:]
                break

        if p_p_id is None:
            raise PyHydroQuebecError("Could not get p_p_id")

        return p_p_id

    def _get_monthly_data(self, p_p_id):
        """Get monthly data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_resource_id": ("resourceObtenirDonnees"
                                      "PeriodesConsommation")}
        try:
            raw_res = requests.get(PROFILE_URL,
                                   params=params,
                                   cookies=self._cookies,
                                   timeout=REQUESTS_TIMEOUT)
        except OSError:
            raise PyHydroQuebecError("Can not get monthly data")
        try:
            json_output = raw_res.json()
        except OSError:
            raise PyHydroQuebecError("Could not get monthly data")

        if not json_output.get('success'):
            raise PyHydroQuebecError("Could not get monthly data")

        return json_output.get('results')

    def _get_daily_data(self, p_p_id, start_date, end_date):
        """Get daily data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_resource_id":
                  "resourceObtenirDonneesQuotidiennesConsommation",
                  "dateDebutPeriode": start_date,
                  "dateFinPeriode": end_date}
        try:
            raw_res = requests.get(PROFILE_URL,
                                   params=params,
                                   cookies=self._cookies,
                                   timeout=REQUESTS_TIMEOUT)
        except OSError:
            raise PyHydroQuebecError("Can not get daily data")
        try:
            json_output = raw_res.json()
        except OSError:
            raise PyHydroQuebecError("Could not get daily data")

        if not json_output.get('success'):
            raise PyHydroQuebecError("Could not get daily data")

        return json_output.get('results')

    def fetch_data(self):
        """Get the latest data from HydroQuebec."""
        # Get login page
        login_url = self._get_login_page()
        # Post login page
        self._post_login_page(login_url)
        # Get p_p_id
        p_p_id = self._get_p_p_id()
        # Get Monthly data
        monthly_data = self._get_monthly_data(p_p_id)[0]
        # Get daily data
        start_date = monthly_data.get('dateDebutPeriode')
        end_date = monthly_data.get('dateFinPeriode')
        daily_data = self._get_daily_data(p_p_id, start_date, end_date)
        daily_data = daily_data[0]['courant']

        # format data
        for key1, key2 in MONTHLY_MAP:
            self._data[key1] = monthly_data[key2]
        for key1, key2 in DAILY_MAP:
            self._data[key1] = daily_data[key2]

    def get_data(self):
        """Return collected data"""
        return self._data
