"""PyHydroQuebec Client Module."""
import asyncio
import datetime
import json
import re

import aiohttp
from bs4 import BeautifulSoup
from dateutil import tz

# Always get the time using HydroQuebec Local Time
HQ_TIMEZONE = tz.gettz('America/Montreal')

REQUESTS_TIMEOUT = 30

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
              ('annual_date_end', 'dateFinAnnee'))


class PyHydroQuebecError(Exception):
    """Base PyHydroQuebec Error."""


class PyHydroQuebecAnnualError(PyHydroQuebecError):
    """Annual PyHydroQuebec Error."""


class HydroQuebecClient():
    """PyHydroQuebec HTTP Client."""

    def __init__(self, username, password, timeout=REQUESTS_TIMEOUT,
                 session=None):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._contracts = []
        self._data = {}
        self._session = session
        self._timeout = timeout

    @asyncio.coroutine
    def _get_httpsession(self):
        """Set http session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

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
            for contract in contracts:
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
        """Get contract number when we have only one contract."""
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
        """Get all balances.

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
            balances.append(float(balance[:-2]
                            .replace(",", ".")
                            .replace("\xa0", "")))

        return balances

    @asyncio.coroutine
    def _load_contract_page(self, contract_url):
        """Load the profile page of a specific contract when we have multiple contracts."""
        try:
            yield from self._session.get(contract_url,
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

        if not json_output.get('results'):
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
    def _get_hourly_data(self, day_date, p_p_id):
        """Get Hourly Data."""
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_state": "normal",
                  "p_p_mode": "view",
                  "p_p_resource_id": "resourceObtenirDonneesConsommationHoraires",
                  "p_p_cacheability": "cacheLevelPage",
                  "p_p_col_id": "column-2",
                  "p_p_col_count": 1,
                  "date": day_date,
                  }
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   params=params,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get hourly data")
        try:
            json_output = yield from raw_res.json(content_type='text/json')
        except (OSError, json.decoder.JSONDecodeError):
            raise PyHydroQuebecAnnualError("Could not get hourly data")
        hourly_consumption_data = json_output['results']['listeDonneesConsoEnergieHoraire']
        hourly_power_data = json_output['results']['listeDonneesConsoPuissanceHoraire']
        params = {"p_p_id": p_p_id,
                  "p_p_lifecycle": 2,
                  "p_p_state": "normal",
                  "p_p_mode": "view",
                  "p_p_resource_id": "resourceObtenirDonneesMeteoHoraires",
                  "p_p_cacheability": "cacheLevelPage",
                  "p_p_col_id": "column-2",
                  "p_p_col_count": 1,
                  "dateDebut": day_date,
                  "dateFin": day_date,
                  }
        try:
            raw_res = yield from self._session.get(PROFILE_URL,
                                                   params=params,
                                                   timeout=self._timeout)
        except OSError:
            raise PyHydroQuebecError("Can not get hourly data")
        try:
            json_output = yield from raw_res.json(content_type='text/json')
        except (OSError, json.decoder.JSONDecodeError):
            raise PyHydroQuebecAnnualError("Could not get hourly data")

        hourly_weather_data = []
        if not json_output.get('results'):
            # Missing Temperature data from Hydro-Quebec (but don't crash the app for that)
            hourly_weather_data = [None]*24
        else:
            hourly_weather_data = json_output['results'][0]['listeTemperaturesHeure']
        # Add temp in data
        processed_hourly_data = [{'hour': data['heure'],
                                  'lower': data['consoReg'],
                                  'high': data['consoHaut'],
                                  'total': data['consoTotal'],
                                  'temp': hourly_weather_data[i]}
                                 for i, data in enumerate(hourly_consumption_data)]

        raw_hourly_data = {'Energy': hourly_consumption_data,
                           'Power': hourly_power_data,
                           'Weather': hourly_weather_data}
        hourly_data = {'processed_hourly_data': processed_hourly_data,
                       'raw_hourly_data': raw_hourly_data}
        return hourly_data

    @asyncio.coroutine
    def fetch_data_detailled_energy_use(self, start_date=None, end_date=None):
        """Get detailled energy use from a specific contract."""
        if start_date is None:
            start_date = datetime.datetime.now(HQ_TIMEZONE) - datetime.timedelta(days=1)
        if end_date is None:
            end_date = datetime.datetime.now(HQ_TIMEZONE)
        # Get http session
        yield from self._get_httpsession()
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
        # For all contracts
        for contract, contract_url in contracts.items():
            if contract_url:
                yield from self._load_contract_page(contract_url)

            data = {}
            dates = [(start_date + datetime.timedelta(n))
                     for n in range(int((end_date - start_date).days))]

            for date in dates:
                # Get Hourly data
                day_date = date.strftime("%Y-%m-%d")
                hourly_data = yield from self._get_hourly_data(day_date, p_p_id)
                data[day_date] = hourly_data['raw_hourly_data']

            # Add contract
            self._data[contract] = data

    @asyncio.coroutine
    def fetch_data(self):
        """Get the latest data from HydroQuebec."""
        # Get http session
        yield from self._get_httpsession()
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
        balances_len = len(balances)
        balance_id = 0
        # For all contracts
        for contract, contract_url in contracts.items():
            if contract_url:
                yield from self._load_contract_page(contract_url)

            # Get Hourly data
            try:
                yesterday = datetime.datetime.now(HQ_TIMEZONE) - datetime.timedelta(days=1)
                day_date = yesterday.strftime("%Y-%m-%d")
                hourly_data = yield from self._get_hourly_data(day_date, p_p_id)
                hourly_data = hourly_data['processed_hourly_data']
            except Exception:  # pylint: disable=W0703
                # We don't have hourly data for some reason
                hourly_data = {}

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
            try:
                daily_data = yield from self._get_daily_data(p_p_id, start_date, end_date)
            except Exception:  # pylint: disable=W0703
                daily_data = []
            # We have to test daily_data because it's empty
            # At the end/starts of a period
            if daily_data:
                daily_data = daily_data[0]['courant']
            # format data
            contract_data = {"balance": balances[balance_id]}
            for key1, key2 in MONTHLY_MAP:
                contract_data[key1] = monthly_data[key2]
            for key1, key2 in ANNUAL_MAP:
                contract_data[key1] = annual_data.get(key2, "")
            # We have to test daily_data because it's empty
            # At the end/starts of a period
            if daily_data:
                for key1, key2 in DAILY_MAP:
                    contract_data[key1] = daily_data[key2]
            # Hourly
            if hourly_data:
                contract_data['yesterday_hourly_consumption'] = hourly_data
            # Add contract
            self._data[contract] = contract_data
            balance_count = balance_id + 1
            if balance_count < balances_len:
                balance_id += 1

    def get_data(self, contract=None):
        """Return collected data."""
        if contract is None:
            return self._data
        if contract in self._data.keys():
            return {contract: self._data[contract]}
        raise PyHydroQuebecError("Contract {} not found".format(contract))

    def get_contracts(self):
        """Return Contract list."""
        return set(self._data.keys())

    async def close_session(self):
        """Close current session."""
        await self._session.close()
