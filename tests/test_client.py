"""Tests for output module."""
import asyncio
import re
import os

from pyhydroquebec.client import HydroQuebecClient


def test_client():
    """Test influx output function."""

    username = os.environ['USERNAME']
    password = os.environ['PASSWORD']
    client = HydroQuebecClient(username, password, 30)

    loop = asyncio.get_event_loop()

    async_func = client.login()
    loop.run_until_complete(asyncio.gather(client.login()))
    assert len(client.customers) > 0
    assert client.customers[0].contrat_id is not None
    assert client.customers[0].account_id is not None


#    async_func = fetch_data(client, args.contract)
#    results = loop.run_until_complete(asyncio.gather(async_func))
#    close_fut = asyncio.wait([client.close_session()])
#    loop.run_until_complete(close_fut)
#    
#
#    assert results
