# Using the lib

First, you need to import the ADSSManager class from the adss module. This class is responsible for loading the available tables from the service and allows you to retrieve them by name.
```python
from adss.tap_manager import TAPManager

core = ADSSManager()
core.load_tables()

core.print_tables()
```

```
[Table(name=delve_dr2, columns=15),
 Table(name=legacy_dr10, columns=13),
 Table(name=splus.splus_dr4, columns=365)]
```


The `load_tables` method will fetch the available tables from the service and store them in the `tables` attribute of the ADSSManager instance. You can access the tables by name using the `get_table` method.
```python
table = core.get_table('delve_dr2')
```

Now the Table object is very powerful and provides several methods to interact with the table. 
For example, retrieving the columns of the table, here we are looking for columns that contain the string "_auto":

```python
table_splus = tap.get_table("splus_dr4")

for column in table_splus.columns:
    if "_auto" in column:
        print(column)

```

```
e_g_auto
e_i_auto
e_j0378_auto
e_j0395_auto
e_j0410_auto
e_j0430_auto
e_j0515_auto
e_j0660_auto
e_j0861_auto
e_r_auto
e_u_auto
e_z_auto
g_auto
i_auto
j0378_auto
j0395_auto
j0410_auto
j0430_auto
j0515_auto
j0660_auto
j0861_auto
r_auto
s2n_det_auto
s2n_g_auto
s2n_i_auto
s2n_j0378_auto
s2n_j0395_auto
s2n_j0410_auto
s2n_j0430_auto
s2n_j0515_auto
s2n_j0660_auto
s2n_j0861_auto
s2n_r_auto
s2n_u_auto
s2n_z_auto
u_auto
z_auto
```

Then you can set the columns and constraints to perform a query. Here we are setting it only for the columns `['id', 'ra', 'dec', 'r_auto', 'i_auto', 'u_auto', 'g_auto', 'z_auto']` on objects with `g_auto` less than 21 and `r_auto` greater than 18:

```python
table_splus.set_columns(['id', 'ra', 'dec', 'r_auto', 'i_auto', 'u_auto', 'g_auto', 'z_auto'])
table_splus.set_constrains("g_auto < 21 AND r_auto > 18")
```

Now you can perform a cone search on the table. Here we are looking for objects within a radius of 10 arcseconds from the position (0, 60):
```python
tab = table_splus.cone_search(
    ra=10, 
    dec=0,
    radius_arcsec=60, 
    method = "sync"
)

print(tab)
```

```
SELECT id,ra,dec,r_auto,i_auto,u_auto,g_auto,z_auto FROM splus.splus_dr4
WHERE 1 = CONTAINS( 
    POINT('ICRS', ra, dec), 
    CIRCLE('ICRS', 10, 0, 60/3600.0) 
) AND (g_auto < 21 and r_auto > 18)

             id                     ra         ...   g_auto    z_auto 
--------------------------- ------------------ ... --------- ---------
DR4_3_STRIPE82-0015_0044044 10.005822088364228 ...  20.99744 19.436935
DR4_3_STRIPE82-0016_0001125  10.00580009891481 ... 20.741268 19.163511
```