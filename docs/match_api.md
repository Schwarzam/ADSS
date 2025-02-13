Following the basic_api tutorial, we will now create a simple match between two db tables and .

First, we need to load the tables from the service and select the columns we want to use in the match. We will use the `set_columns` method to select the columns and the `set_constrains` method to apply filters to the data.

```python
table_splus = tap.get_table("splus")
print("splus columns: ", table_splus.columns)
table_splus.set_columns(['id', 'ra', 'dec', 'r_auto', 'i_auto', 'u_auto', 'g_auto', 'z_auto'])
table_splus.set_constrains("g_auto < 21 and r_auto > 18")

table_delve = tap.get_table("delve")
print("delve columns: ", table_delve.columns)
table_delve.set_columns(['id', 'ra', 'dec'])
table_delve.set_constrains("mag_auto_r > 19")
```

```
splus columns:  ['a', 'b', 'background', 'background_g', 'background_i', 'background_j0378', 'background_j0395', 'background_j0410', 'background_j0430', 'background_j0515', 'background_j0660', 'background_j0861', 'background_r', 'background_u', 'background_z', 'calib_strat', 'class_star', 'dec', 'det_id_dual', 'ebv_sch', 'e_g_aper_3', 'e_g_aper_6', 'e_g_auto', 'e_g_iso', ....... 'z_iso', 'z_petro', 'z_pstotal']
delve columns:  ['dec', 'id', 'mag_auto_g', 'mag_auto_r', 'model_gri', 'model_griz', 'model_grz', 'ra', 'z_phot_err', 'z_phot_l68', 'z_phot_median', 'z_phot_odds', 'z_phot_peak', 'z_phot_samples', 'z_phot_u68']
```

Now we can perform the match between the two tables using the `cross_match` method. The `cross_match` method will return a list of dictionaries with the matched objects.

```python
table_splus.cone_cross_match(
    other_table = table_delve, 
    match_arcsec = 1, 
    ra = 1, 
    dec = 1, 
    radius_arcsec = 100, 
    method = 'sync'
)
```

```
SELECT t1.id, t1.ra, t1.dec, t1.r_auto, t1.i_auto, t1.u_auto, t1.g_auto, t1.z_auto, t2.id, t2.ra, t2.dec
FROM splus.splus_dr4 AS t1, delve_dr2 AS t2
WHERE 1 = CONTAINS(
        POINT('ICRS', t2.ra, t2.dec),
        CIRCLE('ICRS', t1.ra, t1.dec, 1/3600.0)
    )
AND 1 = CONTAINS(
        POINT('ICRS', t1.ra, t1.dec),
        CIRCLE('ICRS', 1, 1, 100/3600.0)
    )
 AND (t1.g_auto < 21 and t1.r_auto > 18)
 AND (t2.mag_auto_r > 19)

             id                     ra         ...       dec_1       
--------------------------- ------------------ ... ------------------
DR4_3_STRIPE82-0004_0041065 0.9917734067430212 ... 0.9772479995295669
DR4_3_STRIPE82-0004_0043869 0.9910551774499052 ... 1.0026249999605028
DR4_3_STRIPE82-0004_0043974 1.0050347067088312 ... 1.0012580009222063
```

