from adss.executors.sync_query import execute_sync
from adss.executors.async_query import execute_async

def cone_search(table, ra, dec, radius):
    if radius < 0:
        raise ValueError("Radius must be positive")
    if radius > 60:
        raise ValueError("Radius must be less than 60 arcsecs")
    
    query = f"""select * from {table}
    WHERE 1 = CONTAINS( POINT('ICRS', ra, dec), 
    CIRCLE('ICRS', {ra}, {dec}, {radius}./3600.))
    """
    return execute_sync(query)

def large_cone_search(table, ra, dec, radius):
    query = f"""select * from {table}
    WHERE 1 = CONTAINS( POINT('ICRS', ra, dec), 
    CIRCLE('ICRS', {ra}, {dec}, {radius}./3600.))
    """
    return execute_async(query)