from __future__ import annotations

from sqlglot import exp, parser
from sqlglot.dialects.dialect import Dialect, build_date_delta, build_formatted_time


# https://docs.vertica.com/24.3.x/en/sql-reference/functions/formatting-functions/to-timestamp/
def _build_to_timestamp(args: list, dialect: Dialect) -> exp.UnixToTime | exp.StrToTime:
    if len(args) == 1:
        return exp.UnixToTime.from_arg_list(args)

    return build_formatted_time(exp.StrToTime)(args, dialect)


class VerticaParser(parser.Parser):
    FUNCTIONS = {
        **parser.Parser.FUNCTIONS,
        "APPROXIMATE_COUNT_DISTINCT": exp.ApproxDistinct.from_arg_list,
        # https://docs.vertica.com/24.3.x/en/sql-reference/functions/data-type-specific-functions/datetime-functions/datediff/
        "DATEDIFF": build_date_delta(exp.DateDiff),
        # https://docs.vertica.com/24.3.x/en/sql-reference/functions/data-type-specific-functions/datetime-functions/timestampdiff/
        "TIMESTAMPDIFF": build_date_delta(exp.TimestampDiff),
        "TO_CHAR": build_formatted_time(exp.TimeToStr),
        "TO_DATE": build_formatted_time(exp.StrToDate),
        "TO_TIMESTAMP": _build_to_timestamp,
    }

    NO_PAREN_FUNCTION_PARSERS = {
        **parser.Parser.NO_PAREN_FUNCTION_PARSERS,
        # https://docs.vertica.com/24.3.x/en/sql-reference/functions/data-type-specific-functions/datetime-functions/sysdate/
        "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp(sysdate=True)),
    }
