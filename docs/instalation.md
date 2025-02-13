# ADSS TAP Query Library

This repository provides a set of tools for querying astronomical TAP services using ADQL. You can perform cone searches, cross-match queries between tables, and even cross-match against user-supplied data. The library supports both synchronous and asynchronous query execution.

## Overview

The main components of the library are:

- **Table Class:**  
  Represents an astronomical table and provides methods to:
  - **Cone Search:** Retrieve objects within a given radius of a specified position.
  - **Cross-Match:** Match objects between two tables using a spatial join.
  - **Table Cross-Match:** Cross-match against a user-supplied table (e.g. an uploaded dataset).

- **TAPManager Class:**  
  Loads available tables (metadata) from a TAP service and allows you to retrieve them by name.

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/schwarzam/adss.git
cd adss
pip install .
```