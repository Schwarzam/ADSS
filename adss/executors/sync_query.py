from adss.variables import BASEURL
from adss.utils.format_table import format_result_table

from astropy.table import Table
from xml.dom import minidom
import requests
import os
import io

from requests.exceptions import Timeout

sync_url = os.path.join(BASEURL, "sync")

def execute_sync(query, timeout=20):
    data = {
        "request": "doQuery",
        "version": "1.0",
        "lang": "ADQL",
        "phase": "run",
        "query": query,
        "format": "csv"
    }

    # Make request to TAP server
    try:
        res = requests.post(sync_url, data=data, timeout=20)
    except Timeout:
        raise Exception("Request to TAP server timed out, for large queries use async query")

    # Handle errors from TAP response
    if res.status_code != 200:
        xmldoc = minidom.parse(io.BytesIO(res.content))
        item = xmldoc.getElementsByTagName("INFO")
        for i in item:
            if i.getAttribute("name") == "QUERY_STATUS" and i.getAttribute("value") == "ERROR":
                error_message = i.firstChild.data
                raise Exception(f"ADQL Query Error: {error_message}")

    # Convert CSV response to Astropy Table
    return format_result_table(Table.read(io.BytesIO(res.content), format="csv"))


