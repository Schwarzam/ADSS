from adss.variables import BASEURL

from astropy.table import Table
from xml.dom import minidom
import requests
import os
import io

sync_url = os.path.join(BASEURL, "sync")

def execute_sync(query):
    data = {
        "request": "doQuery",
        "version": "1.0",
        "lang": "ADQL",
        "phase": "run",
        "query": query,
        "format": "csv"
    }

    # Make request to TAP server
    res = requests.post(sync_url, data=data)

    # Handle errors from TAP response
    if res.status_code != 200:
        xmldoc = minidom.parse(io.BytesIO(res.content))
        item = xmldoc.getElementsByTagName("INFO")
        for i in item:
            if i.getAttribute("name") == "QUERY_STATUS" and i.getAttribute("value") == "ERROR":
                error_message = i.firstChild.data
                raise Exception(f"ADQL Query Error: {error_message}")

    # Convert CSV response to Astropy Table
    return Table.read(io.BytesIO(res.content), format="csv")


