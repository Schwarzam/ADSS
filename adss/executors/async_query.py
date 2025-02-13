from astropy.io.votable import from_table, writeto
from xml.dom import minidom
from astropy.table import Table


from adss.variables import BASEURL
from adss.utils.format_table import format_result_table
import requests
import os

import time

import io

async_url = os.path.join(BASEURL, "async")

def execute_async(query, table_upload=None, refresh_rate=5):
    """Perform async queries on splus cloud TAP service. 

    Args:
        query (str): query itself.
        table_upload (pandas.DataFrame, optional): table to upload. Defaults to None.
        publicdata (bool, optional): If internal wants to access public data. Defaults to None.

    Returns:
        astropy.table.Table: result table.
    """        

    data = {
        "request": 'doQuery',
        "version": '1.0',
        "lang": 'ADQL',
        "phase": 'run',
        "query": query,
        "format": 'csv'
    }

    if str(type(table_upload)) != "<class 'NoneType'>":
        if 'astropy.table' in str(type(table_upload)):
            if len(table_upload) > 6000:
                print('Cutting to the first 6000 objects!')
                table_upload = table_upload[0:6000]
                table_upload = from_table(table_upload)

                IObytes = io.BytesIO()
                writeto(table_upload, IObytes)

                IObytes.seek(0)
            else:
                table_upload = from_table(table_upload)

                IObytes = io.BytesIO()
                writeto(table_upload, IObytes)

                IObytes.seek(0)

        elif 'astropy.io.votable' in str(type(table_upload)):
            if table_upload.get_first_table().nrows > 6000:
                return 'votable bigger than 6000'
            else:
                IObytes = io.BytesIO()
                writeto(table_upload, IObytes)
                IObytes.seek(0)

        elif 'DataFrame' in str(type(table_upload)):
            if len(table_upload) > 6000:
                print('Cutting to the first 6000 objects!')
                table_upload = table_upload[0:6000]
                table_upload = Table.from_pandas(table_upload)
                table_upload = from_table(table_upload)
                IObytes = io.BytesIO()
                writeto(table_upload, IObytes)
                IObytes.seek(0)
            else:
                table_upload = Table.from_pandas(table_upload)
                table_upload = from_table(table_upload)
                IObytes = io.BytesIO()
                writeto(table_upload, IObytes)
                IObytes.seek(0)
                
        else:
            return 'Table type not supported'

        data['upload'] = 'upload,param:uplTable'
        res = requests.post(async_url, data = data, files={'uplTable': IObytes.read()})

    if not table_upload:
        res = requests.post(async_url, data = data)

    xmldoc = minidom.parse(io.BytesIO(res.content))

    try:
        item = xmldoc.getElementsByTagName('phase')[0]
        process = item.firstChild.data

        item = xmldoc.getElementsByTagName('jobId')[0]
        jobID = item.firstChild.data

        while process == 'EXECUTING':
            res = requests.get(os.path.join(async_url, jobID))
            xmldoc = minidom.parse(io.BytesIO(res.content))

            item = xmldoc.getElementsByTagName('phase')[0]
            process = item.firstChild.data
            time.sleep(refresh_rate)

        if process == 'COMPLETED':
            item = xmldoc.getElementsByTagName('result')[0]
            link = item.attributes['xlink:href'].value

            res = requests.get(link)

            return format_result_table(Table.read(io.BytesIO(res.content), format="csv"))

        if process == 'ERROR':
            item = xmldoc.getElementsByTagName('message')[0]
            message = item.firstChild.data

            print("Error: ", message)

    except:
        item = xmldoc.getElementsByTagName('INFO')
        print(item[0].attributes['value'].value, ": ", item[0].firstChild.data)