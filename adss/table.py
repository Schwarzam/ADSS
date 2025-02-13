from adss.executors.sync_query import execute_sync
from adss.executors.async_query import execute_async
from adss.utils import format_table

import re

class Table:
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns
        self.selected_columns = []
        self.constrains = []
        
    def __repr__(self):
        return f"Table(name={self.name}, columns={len(self.columns)})"
    
    def __str__(self):
        return f"Table: {self.name} ({len(self.columns)} columns)"
    
    def check_column(self, column):
        return column in self.columns
    
    def format_columns(self, columns):
        # Use provided columns list rather than an undefined variable
        return ','.join(columns)
    
    def set_columns(self, columns):
        if not isinstance(columns, list):
            columns = [columns]
        for column in columns:
            if not self.check_column(column):
                raise ValueError(f"Column {column} not in table {self.name}, options are {self.columns}")
        self.selected_columns = columns
    
    def set_constrains(self, constrains):
        self.constrains = constrains
    
    def cone_search(self, ra, dec, radius_arcsec, columns=None, method = 'sync'):
        if radius_arcsec < 0:
            raise ValueError("Radius must be positive")
        if radius_arcsec > 60:
            raise ValueError("Radius must be less than 60 arcsecs")
        
        if columns:
            columns_str = self.format_columns(columns)
        elif self.selected_columns:
            columns_str = self.format_columns(self.selected_columns)
        else:
            columns_str = "*"  # Select all columns

        constraints_str = ""
        if self.constrains:
            constraints_str = " AND (" + self.constrains + ")"
            
        query = f"""SELECT {columns_str} FROM {self.name}
WHERE 1 = CONTAINS( 
    POINT('ICRS', ra, dec), 
    CIRCLE('ICRS', {ra}, {dec}, {radius_arcsec}/3600.0) 
){constraints_str}
"""
                
        print(query)
        if method == 'sync':
            return execute_sync(query)
        else:
            return execute_async(query)
    
    def cone_cross_match(
            self, 
            other_table, 
            match_arcsec,
            ra, 
            dec,
            radius_arcsec,
            columns=None, 
            other_columns=None,
            other_suffix=None,
            method='sync'
        ):
        """
        Perform a cone search on the current table (t1) and then cross-match with another table (t2)
        using a matching radius (match_arcsec).
        
        The query first restricts table t1 to a cone centered at (ra, dec) with a radius of radius_arcsec.
        Then, for each object in t1, it finds matching objects in table t2 that lie within match_arcsec 
        of the t1 object's coordinates.
        
        Additionally:
          - If a non-empty `other_suffix` is provided, each selected column from t2 will be aliased with that suffix.
          - The constraints for each table are processed so that the columns in the conditions are properly qualified with t1 or t2.
        
        Parameters:
            other_table (Table): The table to match against (t2).
            match_arcsec (float): The cross-match tolerance radius (in arcseconds) between t1 and t2.
            ra (float): Right Ascension for the cone center (t1).
            dec (float): Declination for the cone center (t1).
            radius_arcsec (float): The cone search radius (in arcseconds) for filtering t1.
            columns (list or None): Columns to select from the current table (t1).
            other_columns (list or None): Columns to select from the other table (t2).
            other_suffix (str or None): Optional suffix to append to each t2 column alias.
            method (str): Use 'sync' for synchronous execution or 'async' for asynchronous.
        
        Returns:
            The result of the query execution via execute_sync or execute_async.
        """
        
        # Helper function to qualify constraint column names with the proper alias.
        # It looks for each column name as a whole word (not already preceded by an alias) and prefixes it.
        def apply_alias_to_constraint(constraint, alias, columns_list):
            for col in columns_list:
                # (?<![\w\.]) ensures that we do not match if the column is already prefixed (like t1.ra)
                pattern = r'(?<![\w\.])\b' + re.escape(col) + r'\b'
                constraint = re.sub(pattern, f"{alias}.{col}", constraint)
            return constraint
        
        # Validate match_arcsec
        if match_arcsec <= 0:
            raise ValueError("Match radius must be positive")
        if match_arcsec > 3:
            print("Match radius may be too large; consider a value less than 3 arcsecs")
        
        # Determine columns for t1
        if columns:
            t1_columns_list = columns if isinstance(columns, list) else [columns]
            t1_columns = ', '.join(f"t1.{col}" for col in t1_columns_list)
        elif self.selected_columns:
            t1_columns = ', '.join(f"t1.{col}" for col in self.selected_columns)
        else:
            t1_columns = "t1.*"
        
        # Determine columns for t2, adding suffix if provided
        if other_columns:
            t2_columns_list = other_columns if isinstance(other_columns, list) else [other_columns]
            if other_suffix:
                t2_columns = ', '.join(f"t2.{col} AS {col}{other_suffix}" for col in t2_columns_list)
            else:
                t2_columns = ', '.join(f"t2.{col}" for col in t2_columns_list)
        elif other_table.selected_columns:
            if other_suffix:
                t2_columns = ', '.join(f"t2.{col} AS {col}{other_suffix}" for col in other_table.selected_columns)
            else:
                t2_columns = ', '.join(f"t2.{col}" for col in other_table.selected_columns)
        else:
            t2_columns = "t2.*"
        
        # Process constraints for t1: apply alias "t1" to each column mentioned in the constraint.
        constraints_t1 = ""
        if self.constrains:
            if isinstance(self.constrains, str):
                processed_constraint = apply_alias_to_constraint(self.constrains, "t1", self.columns)
                constraints_t1 = " AND (" + processed_constraint + ")"
            elif isinstance(self.constrains, list):
                processed_constraints = []
                for c in self.constrains:
                    processed_constraints.append(apply_alias_to_constraint(c, "t1", self.columns))
                constraints_t1 = " AND (" + " AND ".join(processed_constraints) + ")"

        # Process constraints for t2: apply alias "t2" to each column mentioned in the constraint.
        constraints_t2 = ""
        if other_table.constrains:
            if isinstance(other_table.constrains, str):
                processed_constraint = apply_alias_to_constraint(other_table.constrains, "t2", other_table.columns)
                constraints_t2 = " AND (" + processed_constraint + ")"
            elif isinstance(other_table.constrains, list):
                processed_constraints = []
                for c in other_table.constrains:
                    processed_constraints.append(apply_alias_to_constraint(c, "t2", other_table.columns))
                constraints_t2 = " AND (" + " AND ".join(processed_constraints) + ")"
        # Build the query:
        # 1. The first CONTAINS clause performs the cross-match between t1 and t2 with match_arcsec tolerance.
        # 2. The second CONTAINS clause restricts t1 objects to the cone centered at (ra, dec) with radius radius_arcsec.
        query = f"""SELECT {t1_columns}, {t2_columns}
FROM {self.name} AS t1, {other_table.name} AS t2
WHERE 1 = CONTAINS(
        POINT('ICRS', t2.ra, t2.dec),
        CIRCLE('ICRS', t1.ra, t1.dec, {match_arcsec}/3600.0)
    )
AND 1 = CONTAINS(
        POINT('ICRS', t1.ra, t1.dec),
        CIRCLE('ICRS', {ra}, {dec}, {radius_arcsec}/3600.0)
    )
{constraints_t1}
{constraints_t2}
"""
                
        print(query)
        if method == 'async':
            return execute_async(query)
        else:
            return execute_sync(query)
        
    def table_cross_match(
            self, 
            other_table, 
            match_arcsec,
            columns=None, 
            other_columns=None,
            other_suffix=None,
            method='async'
        ):
        """
        Perform a cone search on the current table (t1) and then cross-match with another 
        table (Dataframe or astropy Table) (t2)
        using a matching radius (match_arcsec).
        
        For each object in t1, it finds matching objects in table t2 that lie within match_arcsec 
        of the t1 object's coordinates.
        
        Additionally:
          - If a non-empty `other_suffix` is provided, each selected column from t2 will be aliased with that suffix.
          - The constraints for each table are processed so that the columns in the conditions are properly qualified with t1 or t2.
        
        Parameters:
            other_table (astropy.table.Table): The table to match against (t2).
            match_arcsec (float): The cross-match tolerance radius (in arcseconds) between t1 and t2.
            columns (list or None): Columns to select from the current table (t1).
            other_columns (list or None): Columns to select from the other table (t2).
            other_suffix (str or None): Optional suffix to append to each t2 column alias.
            method (str): Use 'sync' for synchronous execution or 'async' for asynchronous.
        
        Returns:
            The result of the query execution via execute_sync or execute_async.
        """
        
        # Helper function to qualify constraint column names with the proper alias.
        # It looks for each column name as a whole word (not already preceded by an alias) and prefixes it.
        def apply_alias_to_constraint(constraint, alias, columns_list):
            for col in columns_list:
                # (?<![\w\.]) ensures that we do not match if the column is already prefixed (like t1.ra)
                pattern = r'(?<![\w\.])\b' + re.escape(col) + r'\b'
                constraint = re.sub(pattern, f"{alias}.{col}", constraint)
            return constraint
        
        # Validate match_arcsec
        if match_arcsec <= 0:
            raise ValueError("Match radius must be positive")
        if match_arcsec > 3:
            print("Match radius may be too large; consider a value less than 3 arcsecs")
        
        # Determine columns for t1
        if columns:
            t1_columns_list = columns if isinstance(columns, list) else [columns]
            t1_columns = ', '.join(f"t1.{col}" for col in t1_columns_list)
        elif self.selected_columns:
            t1_columns = ', '.join(f"t1.{col}" for col in self.selected_columns)
        else:
            t1_columns = "t1.*"
        
        # Determine columns for t2, adding suffix if provided
        if not other_columns:
            raise ValueError("Must provide columns for the input table (other_columns param)")
        
        if not "ra" in other_columns or not "dec" in other_columns:
            raise ValueError("Input table must have 'ra' and 'dec' columns")
        
        other_table = other_table[other_columns]
        
        t2_columns_list = other_columns if isinstance(other_columns, list) else [other_columns]
        if other_suffix:
            t2_columns = ', '.join(f"t2.{col} AS {col}{other_suffix}" for col in t2_columns_list)
        else:
            t2_columns = ', '.join(f"t2.{col}" for col in t2_columns_list)

        # Process constraints for t1: apply alias "t1" to each column mentioned in the constraint.
        constraints_t1 = ""
        if self.constrains:
            if isinstance(self.constrains, str):
                processed_constraint = apply_alias_to_constraint(self.constrains, "t1", self.columns)
                constraints_t1 = " (" + processed_constraint + ")"
            elif isinstance(self.constrains, list):
                processed_constraints = []
                for c in self.constrains:
                    processed_constraints.append(apply_alias_to_constraint(c, "t1", self.columns))
                constraints_t1 = " (" + " AND ".join(processed_constraints) + ")"

        if constraints_t1:
            constraints_t1 = "WHERE " + constraints_t1
        # Build the query:
        # 1. The first CONTAINS clause performs the cross-match between t1 and t2 with match_arcsec tolerance.
        # 2. The second CONTAINS clause restricts t1 objects to the cone centered at (ra, dec) with radius radius_arcsec.
        query = f"""SELECT {t1_columns}, {t2_columns}
FROM {self.name} AS t1 JOIN tap_upload.upload AS t2 ON
1 = CONTAINS(
        POINT('ICRS', t1.ra, t1.dec),
        CIRCLE('ICRS', t2.ra, t2.dec, {match_arcsec}/3600.0)
    )
{constraints_t1}
"""
                
        print(query)
        if method == 'async':
            return execute_async(query, table_upload=other_table)
        else:
            raise ValueError("Synchronous execution not supported yet for table cross-match")
            #return execute_sync(query)