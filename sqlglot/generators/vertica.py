from __future__ import annotations

from sqlglot import exp, generator
from sqlglot.dialects.dialect import date_delta_sql, rename_func


class VerticaGenerator(generator.Generator):
    TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DataType.Type.INTERVAL: "BIGINT",
    }

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.ApproxDistinct: rename_func("APPROXIMATE_COUNT_DISTINCT"),
        exp.DateDiff: date_delta_sql("DATEDIFF"),
        exp.TimestampDiff: date_delta_sql("TIMESTAMPDIFF"),
        exp.StrToDate: lambda self, e: self.func("TO_DATE", e.this, self.format_time(e)),
        exp.StrToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, self.format_time(e)),
        exp.TimeToStr: lambda self, e: self.func("TO_CHAR", e.this, self.format_time(e)),
        exp.UnixToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this),
    }

    def currenttimestamp_sql(self, expression: exp.CurrentTimestamp) -> str:
        if expression.args.get("sysdate"):
            return "SYSDATE"

        this = expression.this
        return self.func("CURRENT_TIMESTAMP", this) if this else "CURRENT_TIMESTAMP"
