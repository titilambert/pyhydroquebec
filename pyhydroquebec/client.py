"""
PyHydroQuebec
"""
import json
import logging
import re
import asyncio

import aiohttp
from bs4 import BeautifulSoup

REQUESTS_TIMEOUT = 15

HOST = "https://www.hydroquebec.com"
HOME_URL = "{}/portail/web/clientele/authentification".format(HOST)
MAIN_URL = "{}/portail/fr/group/clientele/gerer-mon-compte".format(HOST)
PROFILE_URL = ("{}/portail/fr/group/clientele/"
               "portrait-de-consommation".format(HOST))
MONTHLY_MAP = (('period_total_bill', 'montantFacturePeriode'),
               ('period_projection', 'montantProjetePeriode'),
               ('period_length', 'nbJourLecturePeriode'),
               ('period_total_days', 'nbJourPrevuPeriode'),
               ('period_mean_daily_bill', 'moyenneDollarsJourPeriode'),
               ('period_mean_daily_consumption', 'moyenneKwhJourPeriode'),
               ('period_total_consumption', 'consoTotalPeriode'),
               ('period_lower_price_consumption', 'consoRegPeriode'),
               ('period_higher_price_consumption', 'consoHautPeriode'),
               ('period_average_temperature', 'tempMoyennePeriode'))
DAILY_MAP = (('yesterday_total_consumption', 'consoTotalQuot'),
             ('yesterday_lower_price_consumption', 'consoRegQuot'),
             ('yesterday_higher_price_consumption', 'consoHautQuot'),
             ('yesterday_average_temperature', 'tempMoyenneQuot'))
ANNUAL_MAP = (('annual_mean_daily_consumption', 'moyenneKwhJourAnnee'),
              ('annual_total_consumption', 'consoTotalAnnee'),
              ('annual_total_bill', 'montantFactureAnnee'),
              ('annual_mean_daily_bill', 'moyenneDollarsJourAnnee'),
              ('annual_length', 'nbJourCalendrierAnnee'),
              ('annual_kwh_price_cent', 'coutCentkWh'),
              ('annual_date_start', 'dateDebutAnnee'),
              ('annual_date_end', 'dateDebutAnnee'))


class PyHydroQuebecError(Exception):
    pass


class PyHydroQuebecAnnualError(PyHydroQuebecError):
    pass


class HydroQuebecClient(object):

    def __init__(self, username, password, timeout=REQUESTS_TIMEOUT):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._contracts = []
        self._data = {}
        self._session = None
        self._timeout = timeout

    @asyncio.coroutine
    def _get_login_page(self):
        """Go to the login page."""
        try:
            raw_res = yield from self._session.get(HOME_URL,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not connect to login page")
        # Get login url
        content = yield from raw_res.text()
        soup = BeautifulSoup(content, 'html.parser')
        form_node = soup.find('form', {'name': 'fm'})
        if form_node is None:
            raise PyHydroQuebecError("No login form find")
        login_url = form_node.attrs.get('action')
        if login_url is None:
            raise PyHydroQuebecError("Can not found login url")
        return login_url

    @asyncio.coroutine
    def _post_login_page(self, login_url):
        """Login to HydroQuebec website."""
        data = {"login": self.username,
                "_58_password": self.password}

        try:
            raw_res = yield from self._session.post(login_url,
                                                    data=data,
                                                    timeout=self._timeout,
                                                    allow_redirects=False)
        except OSError:
            raise PyHydroQuebecError("Can not submit login form")
        if raw_res.status != 302:
            raise PyHydroQuebecError("Login error: Bad HTTP status code. "
                                     "Please check your username/password.")
        return True

    @asyncio.coroutine
    def _get_p_p_id_and_contract(self):
        """Get id of consumption profile."""
        contracts = {}
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get profile page")
        # Parse html
        content = yield from raw_res.text()
        soup = BeautifulSoup(content, 'html.parser')
        # Search contracts
        for node in soup.find_all('span', {"class": "contrat"}):
            rematch = re.match("C[a-z]* ([0-9]{4} [0-9]{5})", node.text)
            if rematch is not None:
                contracts[rematch.group(1).replace(" ", "")] = None
        # search for links
        for node in soup.find_all('a', {"class": "big iconLink"}):
            for contract in contracts.keys():
                if contract in node.attrs.get('href'):
                    contracts[contract] = node.attrs.get('href')
        # Looking for p_p_id
        p_p_id = None
        for node in soup.find_all('span'):
            node_id = node.attrs.get('id', "")
            if node_id.startswith("p_portraitConsommation_WAR"):
                p_p_id = node_id[2:]
                break

        if p_p_id is None:
            raise PyHydroQuebecError("Could not get p_p_id")

        return p_p_id, contracts

    @asyncio.coroutine
    def _get_lonely_contract(self):
        """Get contract number when we have only one contract"""
        contracts = {}
        try:
            raw_res = yield from self._session.get(MAIN_URL,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get main page")
        # Parse html
        content = yield from raw_res.text()
        soup = BeautifulSoup(content, 'html.parser')
        info_node = soup.find("div", {"class": "span3 contrat"})
        if info_node is None:
            raise PyHydroQuebecError("Can not found contract")
        research = re.search("Contrat ([0-9]{4} [0-9]{5})", info_node.text)
        if research is not None:
            contracts[research.group(1).replace(" ", "")] = None

        if contracts == {}:
            raise PyHydroQuebecError("Can not found contract")

        return contracts

    @asyncio.coroutine
    def _get_balances(self):
        """Get all balances

        .. todo::

            IT SEEMS balances are shown (MAIN_URL) in the same order
            that contracts in profile page (PROFILE_URL).
            Maybe we should ensure that.
        """
        balances = []
        try:
            raw_res = yield from self._session.get(MAIN_URL,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get main page")
        # Parse html
        content = yield from raw_res.text()
        soup = BeautifulSoup(content, 'html.parser')
        solde_nodes = soup.find_all("div", {"class": "solde-compte"})
        if solde_nodes == []:
            raise PyHydroQuebecError("Can not found balance")
        for solde_node in solde_nodes:
            try:
                balance = solde_node.find("p").text
            except AttributeError:
                raise PyHydroQuebecError("Can not found balance")
            balances.append(float(balance[:-2].replace(",", ".")))

        return balances

    @asyncio.coroutine
    def _load_contract_page(self, contract_url):
        """Load the profile page of a specific contract when we have
        multiple contracts
        """
        try:
            raw_res = yield from self._session.get(contract_url,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get profile page for a "
                                     "specific contract")

    @asyncio.coroutine
    def _get_annual_data(self, p_p_id):
        """Get annual data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_state": "normal",
                  "p_p_mode": "view",
                  "p_p_resource_id": "resourceObtenirDonneesConsommationAnnuelles"}
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   params=params,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecAnnualError("Can not get annual data")
        try:
            json_output = yield from raw_res.json(content_type='text/json')
        except (OSError, json.decoder.JSONDecodeError):
            raise PyHydroQuebecAnnualError("Could not get annual data")

        if not json_output.get('success'):
            raise PyHydroQuebecAnnualError("Could not get annual data")

        if len(json_output.get('results')) < 1:
            raise PyHydroQuebecAnnualError("Could not get annual data")

        if 'courant' not in json_output.get('results')[0]:
            raise PyHydroQuebecAnnualError("Could not get annual data")

        return json_output.get('results')[0]['courant']

    @asyncio.coroutine
    def _get_monthly_data(self, p_p_id):
        """Get monthly data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_resource_id": ("resourceObtenirDonnees"
                                      "PeriodesConsommation")}
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   params=params,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get monthly data")
        try:
            json_output = yield from raw_res.json(content_type='text/json')
        except (OSError, json.decoder.JSONDecodeError):
            raise PyHydroQuebecError("Could not get monthly data")

        if not json_output.get('success'):
            raise PyHydroQuebecError("Could not get monthly data")

        return json_output.get('results')

    @asyncio.coroutine
    def _get_daily_data(self, p_p_id, start_date, end_date):
        """Get daily data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_resource_id":
                  "resourceObtenirDonneesQuotidiennesConsommation",
                  "dateDebutPeriode": start_date,
                  "dateFinPeriode": end_date}
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   params=params,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get daily data")
        try:
            json_output = yield from raw_res.json(content_type='text/json')
        except (OSError, json.decoder.JSONDecodeError):
            raise PyHydroQuebecError("Could not get daily data")

        if not json_output.get('success'):
            raise PyHydroQuebecError("Could not get daily data")

        return json_output.get('results')

    @asyncio.coroutine
    def fetch_data(self):
        """Get the latest data from HydroQuebec."""
        with aiohttp.ClientSession() as session:
            self._session = session
            # Get login page
            login_url = yield from self._get_login_page()
            # Post login page
            yield from self._post_login_page(login_url)
            # Get p_p_id and contracts
            p_p_id, contracts = yield from self._get_p_p_id_and_contract()
            # If we don't have any contrats that means we have only
            # onecontract. Let's get it
            if contracts == {}:
                contracts = yield from self._get_lonely_contract()

            # Get balance
            balances = yield from self._get_balances()
            balance_id = 0
            # For all contracts
            for contract, contract_url in contracts.items():
                if contract_url:
                    yield from self._load_contract_page(contract_url)

                # Get Annual data
                try:
                    annual_data = yield from self._get_annual_data(p_p_id)
                except PyHydroQuebecAnnualError:
                    # We don't have annual data, which is possible if your
                    # contract is younger than 1 year
                    annual_data = {}
                # Get Monthly data
                monthly_data = yield from self._get_monthly_data(p_p_id)
                monthly_data = monthly_data[0]
                # Get daily data
                start_date = monthly_data.get('dateDebutPeriode')
                end_date = monthly_data.get('dateFinPeriode')
                daily_data = yield from self._get_daily_data(p_p_id, start_date, end_date)
                # We have to test daily_data because it's empty
                # At the end/starts of a period
                if len(daily_data) > 0:
                    daily_data = daily_data[0]['courant']

                # format data
                contract_data = {"balance": balances[balance_id]}
                for key1, key2 in MONTHLY_MAP:
                    contract_data[key1] = monthly_data[key2]
                for key1, key2 in ANNUAL_MAP:
                    contract_data[key1] = annual_data.get(key2, "")
                # We have to test daily_data because it's empty
                # At the end/starts of a period
                if len(daily_data) > 0:
                    for key1, key2 in DAILY_MAP:
                        contract_data[key1] = daily_data[key2]
                self._data[contract] = contract_data
                balance_id += 1

    def get_data(self, contract=None):
        """Return collected data"""
        if contract is None:
            return self._data
        elif contract in self._data.keys():
            return {contract: self._data[contract]}
        else:
            raise PyHydroQuebecError("Contract {} not found".format(contract))

    def get_contracts(self):
        return set(self._data.keys())
