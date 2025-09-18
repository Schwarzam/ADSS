# ADSS
Astronomical Data Smart System

ADSS is a database/server project that provides access to ADSS compatible astronomical services.

This repository provides a set of tools for querying astronomical ADSS services using ADQL. You can perform cone searches, cross-match queries between tables, and even cross-match against user-supplied data. The library supports both synchronous and asynchronous query execution. Download of images, cutouts, colored images and spectra is also supported.

Github repository: [https://github.com/schwarzam/adss](https://github.com/schwarzam/adss)

## Installation

```bash
pip install adss
```

or

```bash
git clone https://github.com/schwarzam/adss.git
cd adss
pip install .
```


### About ADSS compatible services

ADSS is a project that is still under development. Currently, some of the ADSS services are available at [https://ai-scope.cbpf.br/](https://ai-scope.cbpf.br/) and [https://splus.cloud/](https://splus.cloud/). 

### New Features

ADSS supports different queries, including cone searches, cross-matches between tables, and cross-matches against user-supplied data. The library supports both synchronous and asynchronous query execution.

Also some improvements in the ADQL parsing were made, allowing queries with wildcards in the SELECT statement, such as:

```sql
SELECT psf_* FROM my_table WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 150.0, 2.0, 0.1))=1
```

This will select all columns that start with "psf_".


### Starting a client

To start using ADSS, you need to initialize a client with the base URL of the ADSS service and your credentials. Here's an example:

```python
import adss

cl = adss.ADSSClient(
    base_url="https://ai-scope.cbpf.br/", 
    username="your_username",
    password="your_password"
)
```

The client will handle authentication and session management for you. 

### Performing Queries

You can perform various types of queries using the client. ADSS inherited a lot of the concept of the Table Access Protocol (TAP). Specially the sync and async modes of queries. 

- **Synchronous Queries** (Short Lived Queries): These queries are executed immediately, and the results are returned in the body of the first request if found! With a timeout of ~10 seconds usually. Good for small tables or queries that return a small number of rows <1000. Example:

```python
cl.query(
"""
select * 
from my_table 
where CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 150.0, 2.0, 0.1))=1
"""
)
```

- **Asynchronous Queries**: These queries are executed in the background, and you can check the status of the query and retrieve the results once they are ready. Good for large tables or queries that return a large number of rows or long queries.

We have two ways of doing async queries. This first send the query to the server and wait until it's done. Example:

```python
tab = cl.query_and_wait(
    query_text="""
    select top 100 * 
    from splus.splus_idr6 where field = 'HYDRA-0091'
    """,
    mode="adql", # or sql
    file=None, # dataframe
    table_name=None,
)
# Print the dataframe
print(tab.data)
```

The second way is a more controlled way, where you create the query, check the status and fetch the when you want results:

```python

# Create a asynchronous query
query = cl.async_query(
    query_text="""
    select top 100 id, ra, dec, mag_psf* 
    from splus.splus_idr6 where field = 'HYDRA-0091'
    """, 
    mode="adql", # or sql
    file=None, # dataframe
    table_name=None, 
)

# Check the status of the query and fetch results if complete
query = cl.queries.get_status(query.id)
if query.is_complete:
    print("Query is complete. Fetching results...")
    results = cl.queries.get_results(query.id)
else:
    print("Query is not complete yet.")

```

### Uploading user tables

In the last example we left the `file` and `table_name` parameters as `None`. This means that we are not uploading any user table to the server. If you want to upload a user table, you can do it by passing a pandas DataFrame to the `file` parameter and a name for the table to the `table_name` parameter. **The uploaded table should be referenced as upload.`table_name` in the query.**.

```python
import pandas as pd
# Create a sample dataframe
data = {
    "id": [1, 2, 3],
    "ra": [150.1, 150.2, 150.3],
    "dec": [2.1, 2.2, 2.3]
}
df = pd.DataFrame(data)

# Create a asynchronous query with user table
query = cl.query_and_wait(
    query_text="""
        select a.*, b.mag_psf_r 
        from upload.my_table as a
        join splus.splus_idr6 as b on a.id = b.id
    """,
    mode="adql", # or sql
    file=df, # dataframe
    table_name="my_table",
)

