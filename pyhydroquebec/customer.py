"""PyHydroQuebec Client Module."""
from datetime import datetime, timedelta
import json
import re

from bs4 import BeautifulSoup
import cachetools

from pyhydroquebec.consts import (ANNUAL_DATA_URL, CONTRACT_CURRENT_URL_1,
                                  CONTRACT_CURRENT_URL_2, CONTRACT_URL_3,
                                  DAILY_DATA_URL, HOURLY_DATA_URL_1,
                                  HOURLY_DATA_URL_2, MONTHLY_DATA_URL,
                                  COMMON_DATA_URL,
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
        """Create new Customer object."""
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
        self._current_common_data = {}
        self._hourly_data = {}

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_summary(self):
        """Fetch data from overview page.

        UI URL: https://session.hydroquebec.com/portail/en/group/clientele/gerer-mon-compte
        """
        self._logger.info("Fetching summary page")
        await self._client.select_customer(self.account_id, self.customer_id)

        res = await self._client.http_request(CONTRACT_URL_3, "get")
        content = await res.text()
        soup = BeautifulSoup(content, 'html.parser')
        try:
            raw_balance = soup.find('p', {'class': 'solde'}).text
            self._balance = float(raw_balance[:-2].replace(",", ".").
                                  replace("\xa0", ""))

            raw_contract_id = soup.find('div', {'class': 'contrat'}).text
            self.contract_id = (raw_contract_id
                                .split("Contrat", 1)[-1]
                                .replace("\t", "")
                                .replace("\n", ""))

        except AttributeError:
            self._logger.info("Customer has no contract")

        # Needs to load the consumption profile page to not break
        # the next loading of the other pages
        await self._client.http_request(CONTRACT_CURRENT_URL_1, "get")

    @property
    def balance(self):
        """Return the collected balance."""
        return self._balance

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_current_period(self):
        """Fetch data of the current period.

        UI URL: https://session.hydroquebec.com/portail/en/group/clientele/portrait-de-consommation
        """
        self._logger.info("Fetching current period data")
        await self._client.select_customer(self.account_id, self.customer_id)

        await self._client.http_request(CONTRACT_CURRENT_URL_1, "get")

        headers = {"Content-Type": "application/json"}
        res = await self._client.http_request(CONTRACT_CURRENT_URL_2, "get", headers=headers)
        text_res = await res.text()
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(text_res)['results'][0]

        self._current_period = {}
        for key, data in CURRENT_MAP.items():
            self._current_period[key] = json_res[data['raw_name']]

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

            if 'compare' in json_res:
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

        self._hourly_data[day_str] = {
                'day_mean_temp': json_res['results'][0]['tempMoyJour'],
                'day_min_temp': json_res['results'][0]['tempMinJour'],
                'day_max_temp': json_res['results'][0]['tempMaxJour'],
                'hours': {},
                }
        tmp_hour_dict = dict((h, {}) for h in range(24))
        for hour, temp in enumerate(json_res['results'][0]['listeTemperaturesHeure']):
            tmp_hour_dict[hour]['average_temperature'] = temp

        params = {"date": day_str}
        res = await self._client.http_request(HOURLY_DATA_URL_1, "get", params=params)
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(await res.text())
        for hour, data in enumerate(json_res['results']['listeDonneesConsoEnergieHoraire']):
            tmp_hour_dict[hour]['lower_price_consumption'] = data['consoReg']
            tmp_hour_dict[hour]['higher_price_consumption'] = data['consoHaut']
            tmp_hour_dict[hour]['total_consumption'] = data['consoTotal']
        self._hourly_data[day_str]['hours'] = tmp_hour_dict.copy()

    @property
    def hourly_data(self):
        """Return collected hourly data."""
        return self._hourly_data

    @cachetools.cached(cachetools.TTLCache(maxsize=128, ttl=60*REQUESTS_TTL))
    async def fetch_common_data(self):
        """Fetch current common data.

        API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
        portrait-de-consommation/resourceObtenirInfoCommunPortrait
        """
        self._logger.info("Fetching common data")
        await self._client.select_customer(self.account_id, self.customer_id)
        headers = {"Content-Type": "application/json"}
        res = await self._client.http_request(COMMON_DATA_URL, "get", headers=headers)
        text_res = await res.text()
        # We can not use res.json() because the response header are not application/json
        json_res = json.loads(text_res)
        if not json_res.get('results'):
            return

        add_hours = 0
        today_message = json_res['results']['zoneMessageHTMLAvisAujourdhui'].replace('&nbsp;',' ')

        if today_message.find("p.m.") != -1 :
            add_hours = 12

        today_list = re.findall(r"\b\d+\b",today_message)
        today_dict = {}

        if len(today_list) >= 4:
            today_dict = {
              "today_start_1": int(today_list[1]),
              "today_end_1": today_list[2],
              "today_start_2": str(int(today_list[3]) + add_hours),
              "today_end_2": str(int(today_list[4]) + add_hours),
            }
        elif len(today_list) >= 2:
            if int(today_list[1]) + add_hours >= 12:
                today_dict = {
                  "today_start_1": "",
                  "today_end_1": "",
                  "today_start_2": str(int(today_list[1]) + add_hours),
                  "today_end_2": str(int(today_list[2]) + add_hours),
                }
            else:
                today_dict = {
                  "today_start_1": today_list[1],
                  "today_end_1": today_list[2],
                  "today_start_2": "",
                  "today_end_2": "",
                }

        add_hours = 0
        tomorrow_message = json_res['results']['zoneMessageHTMLAvisDemain'].replace('&nbsp;',' ')

        if tomorrow_message.find("p.m.") != -1 :
            add_hours = 12

        tomorrow_list = re.findall(r"\b\d+\b",tomorrow_message)
        tomorrow_dict = {}

        if len(tomorrow_list) >= 4:
            tomorrow_dict = {
              "tomorrow_start_1": int(tomorrow_list[1]),
              "tomorrow_end_1": tomorrow_list[2],
              "tomorrow_start_2": str(int(tomorrow_list[3]) + add_hours),
              "tomorrow_end_2": str(int(tomorrow_list[4]) + add_hours),
            }
        elif len(tomorrow_list) >= 2:
            if int(tomorrow_list[1]) + add_hours >= 12:
                tomorrow_dict = {
                  "tomorrow_start_1": "",
                  "tomorrow_end_1": "",
                  "tomorrow_start_2": str(int(tomorrow_list[1]) + add_hours),
                  "tomorrow_end_2": str(int(tomorrow_list[2]) + add_hours),
                }
            else:
                tomorrow_dict = {
                  "tomorrow_start_1": tomorrow_list[1],
                  "tomorrow_end_1": tomorrow_list[2],
                  "tomorrow_start_2": "",
                  "tomorrow_end_2": "",
                }

        self._current_common_data = {
                'tarif_code': json_res['results']['codeTarif'],
                #'adress_line_1': json_res['results']['adresseLieuConsoPartie1'],
                #'adress_line_2': json_res['results']['adresseLieuConsoPartie2'],
                'today_message': json_res['results']['zoneMessageHTMLAvisAujourdhui'].replace('&nbsp;',' '),
                'today_times': json.dumps(today_dict),
                'tomorrow_message': tomorrow_message,
                'tomorrow_times': json.dumps(tomorrow_dict),
                }

    @property
    def current_common_data(self):
        """Return collected current common data."""
        return self._current_common_data
