from sqlglot import parse_one, transpile
import unittest
import sqlglot
from tests.dialects.test_dialect import Validator


class TestVertica(Validator):
    dialect = "vertica"

    def test_vertica_basic(self):
        """Test basic Vertica functionality"""
        self.validate_identity("SELECT 1")
        self.validate_identity("SELECT * FROM users")
        
    def test_vertica_functions(self):
        """Test Vertica-specific functions"""
        # Test DATE_PART function
        self.validate_identity("SELECT DATE_PART('year', created_at) FROM orders")
        
        # Test ILIKE operator  
        self.validate_identity("SELECT * FROM users WHERE `name` ILIKE '%john%'")
        
        # Test APPROXIMATE_COUNT_DISTINCT
        self.validate_identity("SELECT APPROXIMATE_COUNT_DISTINCT(id) FROM users")
        
        # Test NVL function
        self.validate_identity("SELECT NVL(column1, 'default') FROM table1")

    def test_vertica_copy_statements(self):
        """Test Vertica COPY statement support"""
        # Basic COPY FROM
        self.validate_identity(
            "COPY users FROM '/data/users.csv' WITH (DELIMITER ',')"
        )
        
        # COPY TO
        self.validate_identity(
            "COPY users TO '/output/users.txt' WITH (DELIMITER '|')"
        )
        
        # COPY with subquery
        self.validate_identity(
            "COPY (SELECT * FROM users WHERE `active` = TRUE) TO '/output/active.csv' WITH (DELIMITER ',')"
        )
        
        # COPY with advanced options
        self.validate_identity(
            "COPY users FROM '/data/users.csv' WITH (DELIMITER ',', SKIP 1, REJECTMAX 100)"
        )
        
        # COPY with STDIN/STDOUT
        self.validate_identity(
            "COPY users FROM `STDIN` WITH (DELIMITER ',')"
        )
        
        # COPY with file pattern and exceptions
        self.validate_identity(
            "COPY users FROM '/data/*.csv' WITH (DELIMITER ',', EXCEPTIONS '/tmp/exceptions.txt')"
        )

    def test_vertica_enhanced_functions(self):
        """Test enhanced Vertica function support"""
        # Test that functions parse correctly (they may transform to other forms)
        test_cases = [
            # Machine learning functions
            "SELECT SVM_CLASSIFIER('model_name', input_columns) FROM training_data",
            "SELECT KMEANS('k_means_model', features) FROM data_table",
            "SELECT LINEAR_REG('linear_model', predictors, response) FROM dataset",
            
            # Geospatial functions
            "SELECT ST_AREA(polygon_column) FROM geo_table",
            "SELECT ST_DISTANCE(point1, point2) FROM locations",
            "SELECT ST_CONTAINS(polygon, point) FROM spatial_data",
            
            # String functions
            "SELECT EDIT_DISTANCE(string1, string2) FROM text_data",
            "SELECT SOUNDEX(name_column) FROM names_table",
            "SELECT SPLIT_PART(full_name, ' ', 1) FROM users",
            
            # Time series functions
            "SELECT TIME_SLICE(timestamp_col, '1 hour') FROM events",
            "SELECT INTERPOLATE_LINEAR(ts, value_col) FROM timeseries",
        ]
        
        for sql in test_cases:
            try:
                parsed = sqlglot.parse_one(sql, dialect='vertica')
                output = parsed.sql(dialect='vertica')
                # Just ensure it parses and generates valid SQL
                self.assertIsNotNone(parsed)
                self.assertIsNotNone(output)
            except Exception as e:
                self.fail(f"Failed to parse: {sql}. Error: {e}")

    def test_vertica_data_types(self):
        """Test Vertica-specific data types"""
        # Test UUID type
        self.validate_identity("CREATE TABLE users (id UUID, `name` VARCHAR(100))")
        
        # Test geography/geometry types
        self.validate_identity("CREATE TABLE locations (id INTEGER, coordinates GEOGRAPHY)")
        self.validate_identity("CREATE TABLE shapes (id INTEGER, polygon GEOMETRY)")
        
        # Test various numeric types
        self.validate_identity("CREATE TABLE metrics (`value` DOUBLE PRECISION, `count` INTEGER)")

    def test_vertica_advanced_aggregates(self):
        """Test advanced Vertica aggregate functions"""
        # Approximate functions - test the transformed output
        self.validate_identity(
            "SELECT APPROXIMATE_COUNT_DISTINCT(user_id) FROM sessions"
        )
        
        # APPROXIMATE_MEDIAN transforms to APPROXIMATE_PERCENTILE
        sql = "SELECT APPROXIMATE_MEDIAN(response_time) FROM requests"
        parsed = sqlglot.parse_one(sql, dialect='vertica')
        output = parsed.sql(dialect='vertica')
        self.assertEqual(output, "SELECT APPROXIMATE_PERCENTILE(response_time, 0.5) FROM requests")
        
        # Percentile functions
        self.validate_identity(
            "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) FROM employees"
        )
        self.validate_identity(
            "SELECT PERCENTILE_DISC(0.9) WITHIN GROUP (ORDER BY score) FROM tests"
        )

    def test_vertica_transpilation(self):
        """Test transpilation from other dialects to Vertica"""
        # PostgreSQL EXTRACT to Vertica DATE_PART
        pg_sql = "SELECT EXTRACT(year FROM created_at) FROM orders"
        vertica_sql = sqlglot.transpile(pg_sql, read="postgres", write="vertica")[0]
        self.assertEqual(vertica_sql, "SELECT DATE_PART(YEAR, created_at) FROM orders")
        
        # MySQL DATE_FORMAT to Vertica TO_CHAR
        mysql_sql = "SELECT DATE_FORMAT(created_at, '%Y-%m-%d') FROM orders"
        vertica_sql = sqlglot.transpile(mysql_sql, read="mysql", write="vertica")[0]
        self.assertEqual(vertica_sql, "SELECT TO_CHAR(created_at, '%Y-%m-%d') FROM orders")
        
        # Standard EXTRACT to Vertica DATE_PART
        standard_sql = "SELECT EXTRACT('month' FROM created_at) FROM orders"  
        vertica_sql = sqlglot.transpile(standard_sql, read="postgres", write="vertica")[0]
        self.assertEqual(vertica_sql, "SELECT DATE_PART('month', created_at) FROM orders")
        
    def test_vertica_case_sensitivity(self):
        """Test case insensitive behavior"""
        # Both should parse successfully (case insensitive)
        lower = parse_one("select id from users", dialect="vertica")
        upper = parse_one("SELECT ID FROM USERS", dialect="vertica")
        
        # Both should be parsed (not None)
        self.assertIsNotNone(lower)
        self.assertIsNotNone(upper)