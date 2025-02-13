import numpy as np
from astropy.table import Table

def vectorized_string_to_masked_array(column_data):
    """
    Fully vectorized conversion of formatted string arrays to NumPy masked arrays.
    The strings are assumed to be wrapped in curly braces (e.g. "{1,2,3}").
    Any occurrence of the literal "NULL" in a cell will be masked.
    
    Parameters
    ----------
    column_data : numpy.ndarray
        A 1D NumPy array of strings. Each element is a formatted array like "{1,2,3}".
        
    Returns
    -------
    numpy.ma.MaskedArray
        A masked array where "NULL" entries are masked.
    """
    # Remove curly braces (but do not remove "NULL")
    clean_data = np.char.replace(column_data.astype(str), "{", "")
    clean_data = np.char.replace(clean_data, "}", "")
    
    # Split each string by comma into a list of items (with possible surrounding whitespace)
    split_arrays = np.char.split(clean_data, ",")
    
    # --- Determine type by scanning for a first non-"NULL" value ---
    first_value = None
    for row in split_arrays:
        for item in row:
            item_str = item.strip()
            if item_str != "NULL":
                first_value = item_str
                break
        if first_value is not None:
            break
            
    # If no non-NULL value is found, default to a masked object array.
    if first_value is None:
        data = [np.array(row) for row in split_arrays]
        mask = [np.full(len(row), True, dtype=bool) for row in split_arrays]
        return np.ma.masked_array(data, mask=mask)
    
    # Try to determine numeric type.
    # (If first_value consists solely of digits, we'll assume integer.
    #  Otherwise, if it can be converted to float, we'll use float.
    #  Else, we default to string.)
    is_integer = first_value.isdigit()
    is_float = False
    if not is_integer:
        try:
            float(first_value)
            is_float = True
        except Exception:
            pass

    # Prepare lists to store converted rows and corresponding masks.
    data_list = []
    mask_list = []
    
    # Conversion helper functions
    def convert_item(item, conv):
        item = item.strip()
        if item == "NULL":
            return None, True
        else:
            return conv(item), False
    
    if is_integer:
        conv_func = int
        dtype = np.int64
    elif is_float:
        conv_func = float
        dtype = np.float64
    else:
        conv_func = lambda x: x
        dtype = object

    # Process each row
    for row in split_arrays:
        row_vals = []
        row_mask = []
        for item in row:
            val, is_mask = convert_item(item, conv_func)
            # For masked numeric values, we insert a dummy (0 or 0.0) value.
            if is_mask:
                if dtype in (np.int64, np.float64):
                    row_vals.append(0)
                else:
                    row_vals.append("")
            else:
                row_vals.append(val)
            row_mask.append(is_mask)
        # Convert row to an array of the target dtype.
        row_arr = np.array(row_vals, dtype=dtype)
        data_list.append(row_arr)
        mask_list.append(np.array(row_mask, dtype=bool))
    
    # Create and return a masked array.
    return np.ma.masked_array(data_list, mask=mask_list)

def format_result_table(tab):
    if tab is None or len(tab) == 0:
        return None
    
    for col in tab.colnames:
        if len(tab[col]) == 0:
            continue
        if not "<U" in str(tab[col].dtype):
            continue
        
        if "{" in tab[col][0]:
            tab[col] = vectorized_string_to_masked_array(tab[col])

    return tab