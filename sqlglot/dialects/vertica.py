from __future__ import annotations

from sqlglot.dialects.dialect import Dialect, NormalizationStrategy
from sqlglot.generators.vertica import VerticaGenerator
from sqlglot.parsers.vertica import VerticaParser


class Vertica(Dialect):
    NORMALIZATION_STRATEGY = NormalizationStrategy.CASE_INSENSITIVE
    NULL_ORDERING = "nulls_are_large"

    # https://docs.vertica.com/24.3.x/en/sql-reference/functions/formatting-functions/template-patterns-datetime-formatting/
    TIME_MAPPING = {
        "D": "%u",
        "DAY": "%A",
        "DD": "%d",
        "DDD": "%j",
        "DY": "%a",
        "HH": "%I",
        "HH12": "%I",
        "HH24": "%H",
        "IW": "%V",
        "MI": "%M",
        "MM": "%m",
        "MON": "%b",
        "MONTH": "%B",
        "SS": "%S",
        "US": "%f",
        "WW": "%W",
        "YY": "%y",
        "YYYY": "%Y",
    }

    Parser = VerticaParser
    Generator = VerticaGenerator
