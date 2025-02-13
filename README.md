# ADSS
Astronomical Data Smart System

ADSS is a database/server project hosted at CBPF (Brazilian Center for Research in Physics) that provides access to astronomical data from different surveys. 

This repository provides a set of tools for querying astronomical ADSS services using ADQL. You can perform cone searches, cross-match queries between tables, and even cross-match against user-supplied data. The library supports both synchronous and asynchronous query execution.

## Instalation

```bash
pip install adss
```

or

```bash
git clone https://github.com/schwarzam/adss.git
cd adss
pip install .
```

## Tutorials 

We provide a set of tutorials to help you get started with the library:

Perform a simple query to retrieve the available tables from the service, print the columns of a table, set the columns and constraints to perform a query and retrieve the data.
- [Basic API](docs/basic_api.md)

Learn the difference between sync and async queries and when to use each one.
- [Methods of query](docs/sync_async.md)

Perform a raw query to the service.
- [Raw Query](docs/perform_raw_queries.md)

Perform a match between two database tables and a match between a database table and a user input table.
- [Match API](docs/match_api.md)

Perform a match between a database table and a user input table.
- [User Table Input Match](docs/usertable_input_match.md)


## Contributing

We welcome contributions to this project.