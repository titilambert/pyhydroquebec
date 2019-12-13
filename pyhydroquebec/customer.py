"""PyHydroQuebec Client Module."""
from datetime import datetime, timedelta
import json

from bs4 import BeautifulSoup
import cachetools

from pyhydroquebec.consts import (ANNUAL_DATA_URL, CONTRACT_CURRENT_URL_1,
                                  CONTRACT_CURRENT_URL_2, CONTRACT_CURRENT_URL_3,
                                  CONTRACT_URL_3, CONTRACT_URL_4,
                                  DAILY_DATA_URL, HOURLY_DATA_URL_1,
                                  HOURLY_DATA_URL_2, MONTHLY_DATA_URL,
                                  REQUESTS_TTL, DAILY_MAP, MONTHLY_MAP,
                                  ANNUAL_MAP, CURRENT_MAP,
                                  )


class Customer():
    """Represents a HydroQuebec account.

    The account_id is called 'noPartenaireDemandeur' in the HydroQuebec API
    The customer_id is called 'Customer number' in the HydroQuebec 'My accounts' UI
    The contract_id is called 'Contract' in the HydroQuebec 'At a glance' UI
    """

    def __init__(self, client, account_id, customer_id, timeout, logger):
        """Constructor."""
        self._client = client
        self.account_id = account_id
        self.customer_id = customer_id
        self.contract_id = None
        self._timeout = timeout
        self._logger = logger.getChild(customer_id)
        self._balance = None
        self._current_period = {}
        self._current_annual_data = {}
        self._compare_annual_data = {}
        self._current_monthly_data = {}
        self._compare_monthly_data = {}
        self._current_daily_data = {}
        self._compare_daily_data = {}
        self._hourly_data = {}
        self._hourly_data_raw = {}
        self._all_periods_raw = []
        
    @property
    def balance(self):
        """Return the collected balance."""
        return self._balance

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_current_period(self):
        """Fetch data of the current period.

        UI URL: https://session.hydroquebec.com/portail/en/group/clientele/portrait-de-consommation
        """

        await self.fetch_all_periods_raw()

        self._logger.info("Fetching current period data")
       
        json_res = self._all_periods_raw[0]

        self._current_period = {}
        for key, data in CURRENT_MAP.items():
            self._current_period[key] = json_res[data['raw_name']]
    
    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_all_periods_raw(self):
        """Fetch data of all the periods and stored it in raw states

        UI URL: https://session.hydroquebec.com/portail/en/group/clientele/portrait-de-consommation
        """
        self._logger.info("Fetching current period data")
        await self._client.select_customer(self.account_id, self.customer_id)

        params = {'idContrat': '0' + self.contract_id}
        res = await self._client.http_request(CONTRACT_CURRENT_URL_3, "get", params=params)
        text_res = await res.text()

        headers = {"Content-Type": "application/json"}
        res = await self._client.http_request(CONTRACT_CURRENT_URL_2, "get", headers=headers)
        text_res = await res.text()
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(text_res)['results']

        self._all_periods_raw = json_res

    @property
    def current_period(self):
        """Return collected current period data."""
        return self._current_period

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_annual_data(self):
        """Fetch data of the current and last year.

        API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
        portrait-de-consommation/resourceObtenirDonneesConsommationAnnuelles
        """
        self._logger.info("Fetching annual data")
        await self._client.select_customer(self.account_id, self.customer_id)
        headers = {"Content-Type": "application/json"}
        res = await self._client.http_request(ANNUAL_DATA_URL, "get", headers=headers)
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(await res.text())
        if not json_res.get('results'):
            return
        json_res = json_res['results'][0]

        for key, raw_key in ANNUAL_MAP:
            self._current_annual_data[key] = json_res['courant'][raw_key]
            self._compare_annual_data[key] = json_res['compare'][raw_key]

    @property
    def current_annual_data(self):
        """Return collected current year data."""
        return self._current_annual_data

    @property
    def compare_annual_data(self):
        """Return collected previous year data."""
        return self._compare_annual_data

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_monthly_data(self):
        """Fetch data of the current and last year.

        API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
        portrait-de-consommation/resourceObtenirDonneesConsommationMensuelles
        """
        self._logger.info("Fetching monthly data")
        await self._client.select_customer(self.account_id, self.customer_id)
        headers = {"Content-Type": "application/json"}
        res = await self._client.http_request(MONTHLY_DATA_URL, "get", headers=headers)
        text_res = await res.text()
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(text_res)
        if not json_res.get('results'):
            return

        for month_data in json_res.get('results', []):
            month = month_data['courant']['dateDebutMois'][:-3]
            self._current_monthly_data[month] = {}
            if 'compare' in month_data:
                self._compare_monthly_data[month] = {}

            for key, raw_key in MONTHLY_MAP:
                self._current_monthly_data[month][key] = month_data['courant'][raw_key]
                if 'compare' in month_data:
                    self._compare_monthly_data[month][key] = month_data['compare'][raw_key]

    @property
    def current_monthly_data(self):
        """Return collected monthly data of the current year."""
        return self._current_monthly_data

    @property
    def compare_monthly_data(self):
        """Return collected monthly data of the previous year."""
        return self._compare_monthly_data

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_daily_data(self, start_date=None, end_date=None):
        """Fetch data of the current and last year.

        API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
        portrait-de-consommation/resourceObtenirDonneesQuotidiennesConsommation
        """
        self._logger.info("Fetching daily data between %s and %s", start_date, end_date)
        await self._client.select_customer(self.account_id, self.customer_id)
        if start_date is None:
            # Get yesterday
            yesterday = datetime.now() - timedelta(days=1)
            start_date_str = yesterday.strftime("%Y-%m-%d")
        elif hasattr(start_date, "strftime"):
            start_date_str = start_date.strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                print("Start date bad format. It must match %Y-%m-%d")
                return
            start_date_str = start_date

        end_date_str = None
        if end_date is None:
            pass
        elif hasattr(end_date, "strftime"):
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                print("Start date bad format. It must match %Y-%m-%d")
                return
            end_date_str = end_date

        headers = {"Content-Type": "application/json"}
        params = {"dateDebut": start_date_str}
        if end_date_str:
            params.update({"dateFin": end_date_str})
        res = await self._client.http_request(DAILY_DATA_URL, "get",
                                              params=params, headers=headers)
        text_res = await res.text()
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(text_res)
        if not json_res.get('results'):
            return

        for day_data in json_res.get('results', []):
            day = day_data['courant']['dateJourConso']
            self._current_daily_data[day] = {}
            if 'compare' in day_data:
                self._compare_daily_data[day] = {}

            for key, data in DAILY_MAP.items():
                self._current_daily_data[day][key] = day_data['courant'][data['raw_name']]
                if 'compare' in day_data:
                    self._compare_daily_data[day][key] = day_data['compare'][data['raw_name']]

    @property
    def current_daily_data(self):
        """Return collected daily data of the current year."""
        return self._current_daily_data

    @property
    def compare_daily_data(self):
        """Return collected daily data of the previous year."""
        return self._compare_daily_data

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_hourly_data(self, day=None):
        """Fetch data of the current and last year.

        API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
        portrait-de-consommation/resourceObtenirDonneesConsommationHoraires
        """
        self._logger.info("Fetching hourly data for %s", day)
        await self._client.select_customer(self.account_id, self.customer_id)
        await self._client.select_customer(self.account_id, self.customer_id)

        if day is None:
            # Get yesterday
            yesterday = datetime.now() - timedelta(days=1)
            day_str = yesterday.strftime("%Y-%m-%d")
        elif hasattr(day, "strftime"):
            day_str = day.strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(day, "%Y-%m-%d")
            except ValueError:
                print("Start date bad format. It must match %Y-%m-%d")
                return
            day_str = day

        params = {"dateDebut": day_str, "dateFin": day_str}
        res = await self._client.http_request(HOURLY_DATA_URL_2, "get",
                                              params=params, )
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(await res.text())

        if len(json_res.get('results')) == 0:
            self._hourly_data[day_str] = {
                    'day_mean_temp': None,
                    'day_min_temp': None,
                    'day_max_temp': None,
                    'hours': {},
                    }
            tmp_hour_dict = dict((h, {'average_temperature':None}) for h in range(24))
        else:
            self._hourly_data[day_str] = {
                    'day_mean_temp': json_res['results'][0]['tempMoyJour'],
                    'day_min_temp': json_res['results'][0]['tempMinJour'],
                    'day_max_temp': json_res['results'][0]['tempMaxJour'],
                    'hours': {},
                    }
            tmp_hour_dict = dict((h, {}) for h in range(24))
            for hour, temp in enumerate(json_res['results'][0]['listeTemperaturesHeure']):
                tmp_hour_dict[hour]['average_temperature'] = temp

        raw_hourly_weather_data = []
        if len(json_res.get('results')) == 0:
            # Missing Temperature data from Hydro-Quebec (but don't crash the app for that)
            raw_hourly_weather_data = [None]*24
        else:
            raw_hourly_weather_data = json_res['results'][0]['listeTemperaturesHeure']

        params = {"date": day_str}
        res = await self._client.http_request(HOURLY_DATA_URL_1, "get", params=params)
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(await res.text())
        for hour, data in enumerate(json_res['results']['listeDonneesConsoEnergieHoraire']):
            tmp_hour_dict[hour]['lower_price_consumption'] = data['consoReg']
            tmp_hour_dict[hour]['higher_price_consumption'] = data['consoHaut']
            tmp_hour_dict[hour]['total_consumption'] = data['consoTotal']
        self._hourly_data[day_str]['hours'] = tmp_hour_dict.copy()

        #Also copy the raw hourly data from hydroquebec (This can be used later for commercial accounts, mostly 15 minutes power data)
        self._hourly_data_raw[day_str] = {
            'Energy': json_res['results']['listeDonneesConsoEnergieHoraire'],
            'Power': json_res['results']['listeDonneesConsoPuissanceHoraire'],
            'Weather': raw_hourly_weather_data
        }

    @property
    def hourly_data(self):
        """Return collected hourly data."""
        return self._hourly_data

@cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
async def create_customers_from_summary(client, account_id, customer_id, timeout, logger):
    """Create all customers objects inside a list."""
    logger.info("Fetching summary page")

    customers = []

    await client.select_customer(account_id, customer_id)

    res = await client.http_request(CONTRACT_URL_3, "get")
    content = await res.text()
    soup = BeautifulSoup(content, 'html.parser')

    #1st determine if it's a multi contract holder
    if soup.find('h2', {'class': 'entete-multi-compte'}):
        #It's a multi account so we need to create multiple customer objects
        accounts = soup.find_all('article', {'class': 'compte'})
        for account in accounts:
            try:
                account_ncc = account.get('id')[7:]
                raw_balance = account.find('p', {'class': 'solde'}).text
                balance = float(raw_balance[:-2].replace(",", ".").
                                replace("\xa0", ""))
                #time to get the contract id from the special ajax request
                params = {'ncc':account_ncc}
                res2 = await  client.http_request(CONTRACT_URL_4, "get",
                                params=params)
                content2 = await res2.text()
                soup2 = BeautifulSoup(content2, 'html.parser')
                raw_contract_id = soup2.find('div', {'class': 'contrat'}).text
                contract_id = (raw_contract_id
                            .split("Contrat", 1)[-1]
                            .replace("\t", "")
                            .replace("\n", ""))
                #Time to create the customer object
                customer = Customer(client, account_id, customer_id, timeout, logger)
                customer.contract_id = contract_id
                customer._balance = balance
                customers.append(customer)
            except AttributeError:
                logger.info("Customer has no contract")
    else:
        try:
            raw_balance = soup.find('p', {'class': 'solde'}).text
            balance = float(raw_balance[:-2].replace(",", ".").
                                replace("\xa0", ""))

            raw_contract_id = soup.find('div', {'class': 'contrat'}).text
            contract_id = (raw_contract_id
                                .split("Contrat", 1)[-1]
                                .replace("\t", "")
                                .replace("\n", ""))
            customer = Customer(client, account_id, customer_id, timeout, logger)
            customer.contract_id = contract_id
            customer._balance = balance
            customers.append(customer)
        except AttributeError:
            logger.info("Customer has no contract")
    
    # Needs to load the consumption profile page to not break
    # the next loading of the other pages
    await client.http_request(CONTRACT_CURRENT_URL_1, "get")

    return customers
