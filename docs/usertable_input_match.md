Now, it is also possible to perform a match between a database table and a user input table. The user input table can be a pandas DataFrame or a astropy.table.Table.

```python
table_splus = tap.get_table("splus_dr4")
print("splus columns: ", table_splus.columns)
table_splus.set_columns(['id', 'ra', 'dec', 'r_auto', 'i_auto', 'u_auto', 'g_auto', 'z_auto'])
table_splus.set_constrains("g_auto < 21")

tab = table_splus.table_cross_match(
    user_tab,
    match_arcsec=2,
    other_columns=['id', 'ra', 'dec'],
)
```

```
splus columns:  ['a', 'b', 'background', 'background_g', 'background_i', 'background_j0378', 'background_j0395', 'background_j0410', 'background_j0430', 'background_j0515', .....'z_petro', 'z_pstotal']

SELECT t1.id, t1.ra, t1.dec, t1.r_auto, t1.i_auto, t1.u_auto, t1.g_auto, t1.z_auto, t2.id, t2.ra, t2.dec
FROM splus.splus_dr4 AS t1 JOIN tap_upload.upload AS t2 ON
1 = CONTAINS(
        POINT('ICRS', t1.ra, t1.dec),
        CIRCLE('ICRS', t2.ra, t2.dec, 2/3600.0)
    )
WHERE  (t1.g_auto < 22)

id                      ra          ...         dec_1        
--------------------------- -------------------- ... ---------------------
DR4_3_STRIPE82-0001_0030301   359.99739121534384 ... -0.009413499999979535
DR4_3_STRIPE82-0001_0030225 0.008966701295117348 ... -0.013203499999761448

```