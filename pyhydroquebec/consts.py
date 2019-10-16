"""PyHydroQuebec Consts."""
from dateutil import tz


# Always get the time using HydroQuebec Local Time
HQ_TIMEZONE = tz.gettz('America/Montreal')

REQUESTS_TIMEOUT = 30
REQUESTS_TTL = 1

HOST_LOGIN = "https://connexion.hydroquebec.com"
HOST_SESSION = "https://session.hydroquebec.com"
HOST_SERVICES = "https://cl-services.idp.hydroquebec.com"
HOST_SPRING = "https://cl-ec-spring.hydroquebec.com"

LOGIN_URL_1 = "{}/hqam/XUI/".format(HOST_LOGIN)
LOGIN_URL_2 = "{}/hqam/json/serverinfo/*".format(HOST_LOGIN)
LOGIN_URL_3 = "{}/hqam/json/realms/root/realms/clients/authenticate".format(HOST_LOGIN)
LOGIN_URL_4 = "{}/config/security.json".format(HOST_SESSION)
LOGIN_URL_5 = "{}/hqam/oauth2/authorize".format(HOST_LOGIN)
LOGIN_URL_6 = "{}/cl/prive/api/v3_0/conversion/codeAcces".format(HOST_SERVICES)
LOGIN_URL_7 = "{}/cl/prive/api/v1_0/relations".format(HOST_SERVICES)

CONTRACT_URL_1 = "{}/cl/prive/api/v3_0/partenaires/infoBase".format(HOST_SERVICES)
CONTRACT_URL_2 = "{}/portail/prive/maj-session/".format(HOST_SPRING)
CONTRACT_URL_3 = "{}/portail/fr/group/clientele/gerer-mon-compte/".format(HOST_SPRING)

CONTRACT_CURRENT_URL_1 = ("{}/portail/fr/group/clientele/"
                          "portrait-de-consommation".format(HOST_SPRING))
CONTRACT_CURRENT_URL_2 = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                          "resourceObtenirDonneesPeriodesConsommation".format(HOST_SPRING))

ANNUAL_DATA_URL = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                   "resourceObtenirDonneesConsommationAnnuelles".format(HOST_SPRING))

MONTHLY_DATA_URL = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                    "resourceObtenirDonneesConsommationMensuelles".format(HOST_SPRING))

DAILY_DATA_URL = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                  "resourceObtenirDonneesQuotidiennesConsommation".format(HOST_SPRING))

HOURLY_DATA_URL_1 = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                     "resourceObtenirDonneesConsommationHoraires".format(HOST_SPRING))
HOURLY_DATA_URL_2 = ("{}/portail/fr/group/clientele/portrait-de-consommation/"
                     "resourceObtenirDonneesMeteoHoraires".format(HOST_SPRING))




CURRENT_MAP = (('period_total_bill', 'montantFacturePeriode'),
               ('period_projection', 'montantProjetePeriode'),
               ('period_length', 'nbJourLecturePeriode'),
               ('period_total_days', 'nbJourPrevuPeriode'),
               ('period_mean_daily_bill', 'moyenneDollarsJourPeriode'),
               ('period_mean_daily_consumption', 'moyenneKwhJourPeriode'),
               ('period_total_consumption', 'consoTotalPeriode'),
               ('period_lower_price_consumption', 'consoRegPeriode'),
               ('period_higher_price_consumption', 'consoHautPeriode'),
               ('period_average_temperature', 'tempMoyennePeriode'))
MONTHLY_MAP = (('conso_code', 'codeConsoMois'),
               ('nb_day', 'nbJourCalendrierMois'),
               ('temperature_mean', 'tempMoyenneMois'),
               ('mean_consumption_per_day', 'moyenneKwhJourMois'),
               ('lower_price_consumption', 'consoRegMois'),
               ('higher_price_consumption', 'consoHautMois'),
               ('total_consumption', 'consoTotalMois'),
               )

DAILY_MAP = (('total_consumption', 'consoTotalQuot'),
             ('lower_price_consumption', 'consoRegQuot'),
             ('higher_price_consumption', 'consoHautQuot'),
             ('average_temperature', 'tempMoyenneQuot'))
ANNUAL_MAP = (('annual_mean_daily_consumption', 'moyenneKwhJourAnnee'),
              ('annual_total_consumption', 'consoTotalAnnee'),
              ('annual_total_bill', 'montantFactureAnnee'),
              ('annual_mean_daily_bill', 'moyenneDollarsJourAnnee'),
              ('annual_length', 'nbJourCalendrierAnnee'),
              ('annual_kwh_price_cent', 'coutCentkWh'),
              ('annual_date_start', 'dateDebutAnnee'),
              ('annual_date_end', 'dateFinAnnee'))

OVERVIEW_TPL = ("""
##################################
# Hydro Quebec data for contract #
# {0.contract_id}
##################################

Account ID: {0.account_id}
Customer number: {0.customer_id}
Contract: {0.contract_id}
===================

Balance: {0.balance:.2f} $
""")

CONSUMPTION_PROFILE_TPL = ("""
Period Info
===========
Period day number:      {d[period_length]:d}
Period total days:      {d[period_total_days]:d} days
Period mean temperate:  {d[period_average_temperature]:.1f} C

Period current bill
===================
Total Bill:             {d[period_total_bill]:.2f} $
Projection bill:        {d[period_projection]:.2f} $
Mean Daily Bill:        {d[period_mean_daily_bill]:.2f} $

Total period consumption
========================
Lower price:            {d[period_lower_price_consumption]:.2f} kWh
Higher price:           {d[period_higher_price_consumption]:.2f} kWh
Total:                  {d[period_total_consumption]:.2f} kWh
Mean daily:             {d[period_mean_daily_consumption]:.2f} kWh
""")


YESTERDAY_TPL = ("""
Yesterday consumption
=====================    
Temperature:            {d[yesterday_average_temperature]:d} °C
Lower price:            {d[yesterday_lower_price_consumption]:.2f} kWh
Higher price:           {d[yesterday_higher_price_consumption]:.2f} kWh
Total:                  {d[yesterday_total_consumption]:.2f} kWh
""")

HOURLY_TPL = ("""
Yesterday consumption details
-----------------------------
   Hour  | Temperature | Lower price consumption | Higher price consumption | total comsumption
""")

ANNUAL_TPL = ("""
Annual Total
============

Start date:             {d[annual_date_start]}
End date:               {d[annual_date_end]}
Total bill:             {d[annual_total_bill]} $
Mean daily bill:        {d[annual_mean_daily_bill]} $
Total consumption:      {d[annual_total_consumption]} kWh
Mean dailyconsumption:  {d[annual_mean_daily_consumption]} kWh
kWh price:              {d[annual_kwh_price_cent]} ¢
""")
