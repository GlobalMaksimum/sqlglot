from sqlglot import exp
from tests.dialects.test_dialect import Validator


class TestVertica(Validator):
    dialect = "vertica"

    def test_vertica(self):
        self.validate_identity('SELECT "col" FROM "t"')

        self.validate_all(
            "SELECT fname, lname, age FROM person ORDER BY age DESC, fname ASC, lname NULLS FIRST",
            read={
                "hive": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
            },
            write={
                "hive": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
            },
        )

        self.validate_identity("SELECT APPROXIMATE_COUNT_DISTINCT(x)")
        self.validate_identity("SELECT APPROXIMATE_COUNT_DISTINCT(x, 2.0)")

        self.validate_identity("SYSDATE").assert_is(exp.CurrentTimestamp)
        self.validate_identity("SELECT SYSDATE")

        self.validate_identity("SELECT DATEDIFF(YEAR, a, b)")
        self.validate_all(
            "SELECT DATEDIFF(YEAR, a, b)",
            read={"snowflake": "SELECT DATEDIFF(year, a, b)"},
        )

        self.validate_identity("SELECT TIMESTAMPDIFF(HOUR, a, b)")

        self.validate_identity("SELECT TO_CHAR(x, 'YYYY-MM-DD')")
        self.validate_identity("SELECT TO_DATE(x, 'YYYY-MM-DD')")
        self.validate_identity("SELECT TO_TIMESTAMP(1234567890)")
        self.validate_identity("SELECT TO_TIMESTAMP(x, 'YYYY-MM-DD HH24:MI:SS')")
