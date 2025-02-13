import requests
import pprint
import os

import xml.etree.ElementTree as ET

from adss.table import Table
from adss.variables import BASEURL

class ADSSManager:
    def __init__(self):
        self.tables = {}
        
    def load_tables(self):
        res = requests.get(os.path.join(BASEURL, 'tables'))
        
        # Parse the XML
        root = ET.fromstring(res.content)

        # In this XML, the root element is in the "vosi" namespace but the child elements (schema, table, etc.)
        # are unqualified (i.e. have no prefix). Thus, we can search for them without a namespace.
        tables = []
        for schema_elem in root.findall('schema'):
            schema_name = schema_elem.find('name').text if schema_elem.find('name') is not None else None
            
            for table_elem in schema_elem.findall('table'):
                table_name = table_elem.find('name').text if table_elem.find('name') is not None else None
                columns = []
                for col_elem in table_elem.findall('column'):
                    col_name = col_elem.find('name').text if col_elem.find('name') is not None else None
                    #dataType_elem = col_elem.find('dataType')
                    #data_type = dataType_elem.text if dataType_elem is not None else None
                    # The xsi:type attribute is in the XML namespace for xsi
                    #xsi_type = dataType_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type') if dataType_elem is not None else None
                    columns.append(col_name)
                
                if schema_name == "public":
                    name = table_name
                else:
                    name = f"{schema_name}.{table_name}"
                    
                tables.append(Table(name, columns))

        self.tables = tables
        
    def print_tables(self):
        pprint.pprint(self.tables)
    
    def get_table(self, name):
        for table in self.tables:
            if name in table.name:
                return table
        return None