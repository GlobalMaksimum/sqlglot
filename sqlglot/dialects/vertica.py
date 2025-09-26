
import typing as t

from sqlglot import exp, generator, parser, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
    build_formatted_time,
    rename_func,
    timestamptrunc_sql,
    unit_to_str,
)
from sqlglot.helper import seq_get


class Vertica(Dialect):
    """
    Vertica SQL dialect implementation for SQLGlot.
    
    Vertica is an analytic database management platform designed for big data analytics.
    This dialect implements Vertica-specific SQL syntax and functions.
    
    Key features supported:
    - Case-insensitive SQL parsing
    - Vertica-specific functions (DATE_PART, APPROXIMATE_COUNT_DISTINCT, NVL, etc.)
    - ILIKE operator for case-insensitive pattern matching
    - Window/analytic functions
    - Vertica data types (UUID, TIMESTAMPTZ, LONG VARCHAR, etc.)
    - COPY statements for bulk data loading/export (without INTO keyword)
    - Cross-dialect transpilation
    """
    
    NORMALIZATION_STRATEGY = NormalizationStrategy.CASE_INSENSITIVE
    
    # Vertica supports standard SQL with some extensions
    SUPPORTS_COLUMN_JOIN_MARKS = False
    SUPPORTS_SEMI_ANTI_JOIN = True
    
    class Tokenizer(tokens.Tokenizer):
        QUOTES = ["'", '"']
        IDENTIFIERS = ["`", '"']
        
        # Vertica-specific string literals
        STRING_ESCAPES = ["'", "\\"]
        
        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            # Vertica-specific keywords (using available token types)
            "SEGMENTED": tokens.TokenType.PARTITION_BY,  # Vertica table segmentation
            "REFRESH": tokens.TokenType.REFRESH,
            "OVER": tokens.TokenType.OVER,
            "COPY": tokens.TokenType.COPY,
            # Vertica projection and table keywords
            "PROJECTION": tokens.TokenType.VIEW,  # Vertica projections
            "PROJECTIONS": tokens.TokenType.VIEW,
            "KSAFE": tokens.TokenType.VAR,
            "UNSEGMENTED": tokens.TokenType.VAR,
            # Vertica data loading keywords  
            "DELIMITER": tokens.TokenType.VAR,
            "ENCLOSED": tokens.TokenType.VAR,
            "ESCAPE": tokens.TokenType.VAR,
            "FILLER": tokens.TokenType.VAR,
            "REJECTED": tokens.TokenType.VAR,
            "EXCEPTIONS": tokens.TokenType.VAR,
            "REJECTMAX": tokens.TokenType.VAR,
            "SKIP": tokens.TokenType.OFFSET,
            "TRAILING": tokens.TokenType.VAR,
            "NULLCOLS": tokens.TokenType.VAR,
            # Vertica node and cluster keywords
            "NODE": tokens.TokenType.VAR,
            "NODES": tokens.TokenType.VAR,
            "LOCAL": tokens.TokenType.VAR,
            "GLOBAL": tokens.TokenType.VAR,
        }

    class Parser(parser.Parser):
        FUNCTIONS = {
            **parser.Parser.FUNCTIONS,
            # Vertica-specific functions
            "APPROXIMATE_COUNT_DISTINCT": exp.Hll.from_arg_list,
            "APPROXIMATE_MEDIAN": lambda args: exp.ApproxQuantile(
                this=seq_get(args, 0), quantile=exp.Literal.number(0.5)
            ),
            "APPROXIMATE_PERCENTILE": exp.ApproxQuantile.from_arg_list,
            "DECODE": exp.Case.from_arg_list,
            "DATEDIFF": lambda args: exp.DateDiff(
                this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
            ),
            "DATE_PART": lambda args: exp.Extract(
                this=seq_get(args, 0), expression=seq_get(args, 1)
            ),
            "DATE_TRUNC": lambda args: exp.DateTrunc(
                unit=seq_get(args, 0), this=seq_get(args, 1)
            ),
            "EXTRACT": lambda args: exp.Extract(
                this=seq_get(args, 0), expression=seq_get(args, 1)
            ),
            "GETDATE": exp.CurrentTimestamp.from_arg_list,
            "HASH": exp.MD5.from_arg_list,
            "ILIKE": lambda args: exp.ILike(this=seq_get(args, 0), expression=seq_get(args, 1)),
            "INSTR": exp.StrPosition.from_arg_list,
            "LENGTH": exp.Length.from_arg_list,
            "MADLIB": exp.Anonymous.from_arg_list,
            "MONTHS_BETWEEN": lambda args: exp.DateDiff(
                this=seq_get(args, 0), expression=seq_get(args, 1), unit=exp.Literal.string("MONTH")
            ),
            "NVL": exp.Coalesce.from_arg_list,
            "NVL2": lambda args: exp.Case().when(
                exp.Is(this=seq_get(args, 0) or exp.Null(), expression=exp.Null()), seq_get(args, 2) or exp.Null()
            ).else_(seq_get(args, 1) or exp.Null()),
            "REGEXP_COUNT": exp.RegexpExtract.from_arg_list,
            "REGEXP_INSTR": exp.RegexpExtract.from_arg_list,
            "REGEXP_SUBSTR": exp.RegexpExtract.from_arg_list,
            "SQUARE": lambda args: exp.Pow(this=seq_get(args, 0), expression=exp.Literal.number(2)),
            "TO_CHAR": build_formatted_time(exp.TimeToStr, "vertica"),
            "TO_DATE": build_formatted_time(exp.TsOrDsToDate, "vertica"),
            "TO_HEX": exp.Hex.from_arg_list,
            "TO_NUMBER": exp.Cast.from_arg_list,
            "TO_TIMESTAMP": build_formatted_time(exp.StrToTime, "vertica"),
            "TRUNC": lambda args: exp.DateTrunc(
                unit=seq_get(args, 1) or exp.Literal.string("DD"), this=seq_get(args, 0)
            ),
            "TIMESTAMPDIFF": lambda args: exp.DateDiff(
                this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
            ),
            # Vertica analytic functions
            "FIRST_VALUE": exp.FirstValue.from_arg_list,
            "LAST_VALUE": exp.LastValue.from_arg_list,
            "LAG": exp.Lag.from_arg_list,
            "LEAD": exp.Lead.from_arg_list,
            "RANK": exp.Rank.from_arg_list,
            "ROW_NUMBER": exp.RowNumber.from_arg_list,
            "DENSE_RANK": exp.DenseRank.from_arg_list,
            "NTILE": exp.Ntile.from_arg_list,
            "PERCENT_RANK": exp.PercentRank.from_arg_list,
            "CUME_DIST": exp.CumeDist.from_arg_list,
            # Vertica time series functions
            "TS_FIRST_VALUE": exp.FirstValue.from_arg_list,
            "TS_LAST_VALUE": exp.LastValue.from_arg_list,
            "INTERPOLATE_LINEAR": exp.Anonymous.from_arg_list,
            "INTERPOLATE_CONSTANT": exp.Anonymous.from_arg_list,
            "TIME_SLICE": exp.Anonymous.from_arg_list,
            
            # Vertica machine learning functions
            "SVM_CLASSIFIER": exp.Anonymous.from_arg_list,
            "SVM_REGRESSOR": exp.Anonymous.from_arg_list,
            "KMEANS": exp.Anonymous.from_arg_list,
            "LINEAR_REG": exp.Anonymous.from_arg_list,
            "LOGISTIC_REG": exp.Anonymous.from_arg_list,
            "RF_CLASSIFIER": exp.Anonymous.from_arg_list,
            "RF_REGRESSOR": exp.Anonymous.from_arg_list,
            "NAIVE_BAYES": exp.Anonymous.from_arg_list,
            
            # Vertica geospatial functions
            "ST_AREA": exp.Anonymous.from_arg_list,
            "ST_ASTEXT": exp.Anonymous.from_arg_list,
            "ST_BUFFER": exp.Anonymous.from_arg_list,
            "ST_CONTAINS": exp.Anonymous.from_arg_list,
            "ST_DISTANCE": exp.Anonymous.from_arg_list,
            "ST_GEOMFROMTEXT": exp.Anonymous.from_arg_list,
            "ST_INTERSECTS": exp.Anonymous.from_arg_list,
            "ST_LENGTH": exp.Anonymous.from_arg_list,
            "ST_POINT": exp.Anonymous.from_arg_list,
            "ST_WITHIN": exp.Anonymous.from_arg_list,
            
            # Vertica string and conversion functions
            "ASCII": exp.Anonymous.from_arg_list,
            "BIT_LENGTH": exp.Anonymous.from_arg_list,
            "BTRIM": exp.Trim.from_arg_list,
            "CHARACTER_LENGTH": exp.Length.from_arg_list,
            "CHR": exp.Anonymous.from_arg_list,
            "EDIT_DISTANCE": exp.Anonymous.from_arg_list,
            "INITCAP": exp.Anonymous.from_arg_list,
            "JARO_DISTANCE": exp.Anonymous.from_arg_list,
            "JARO_WINKLER_DISTANCE": exp.Anonymous.from_arg_list,
            "LEVENSHTEIN_DISTANCE": exp.Anonymous.from_arg_list,
            "LTRIM": exp.Anonymous.from_arg_list,
            "OCTET_LENGTH": exp.Anonymous.from_arg_list,
            "POSITION": exp.StrPosition.from_arg_list,
            "REPEAT": exp.Anonymous.from_arg_list,
            "RTRIM": exp.Anonymous.from_arg_list,
            "SOUNDEX": exp.Anonymous.from_arg_list,
            "SPLIT_PART": exp.Anonymous.from_arg_list,
            "STRPOS": exp.StrPosition.from_arg_list,
            
            # Vertica mathematical functions
            "CBRT": exp.Anonymous.from_arg_list,
            "DEGREES": exp.Anonymous.from_arg_list,
            "LOG": exp.Log.from_arg_list,  
            "RADIANS": exp.Anonymous.from_arg_list,
            "RANDOM": exp.Rand.from_arg_list,
            "ROUND": exp.Round.from_arg_list,
            "SIGN": exp.Anonymous.from_arg_list,
            "SQRT": exp.Sqrt.from_arg_list,
            "TRUNC": exp.Anonymous.from_arg_list,
            
            # Vertica aggregate functions
            "APPROXIMATE_MEDIAN": lambda args: exp.ApproxQuantile(
                this=seq_get(args, 0), quantile=exp.Literal.number(0.5)
            ),
            "APPROXIMATE_PERCENTILE": exp.ApproxQuantile.from_arg_list,
            "LISTAGG": exp.GroupConcat.from_arg_list,
            "MEDIAN": exp.Anonymous.from_arg_list,
            "PERCENTILE_CONT": exp.PercentileCont.from_arg_list,
            "PERCENTILE_DISC": exp.PercentileDisc.from_arg_list,
            "STDDEV": exp.Stddev.from_arg_list,
            "STDDEV_POP": exp.StddevPop.from_arg_list,
            "STDDEV_SAMP": exp.StddevSamp.from_arg_list,
            "VARIANCE": exp.Variance.from_arg_list,
            "VAR_POP": exp.VariancePop.from_arg_list,
            "VAR_SAMP": exp.Anonymous.from_arg_list,
        }



    class Generator(generator.Generator):
        # Vertica COPY statement does not use INTO keyword
        COPY_HAS_INTO_KEYWORD = False
        
        TRANSFORMS = {
            **generator.Generator.TRANSFORMS,
            exp.Hll: rename_func("APPROXIMATE_COUNT_DISTINCT"),
            exp.ApproxQuantile: rename_func("APPROXIMATE_PERCENTILE"),
            exp.Coalesce: rename_func("NVL"),
            exp.CurrentTimestamp: rename_func("GETDATE"),
            exp.DateDiff: lambda self, e: self.func(
                "DATEDIFF", unit_to_str(e), e.this, e.expression
            ),
            exp.DateTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
            exp.Extract: lambda self, e: self.func("DATE_PART", e.this, e.expression),
            exp.Hex: rename_func("TO_HEX"),
            exp.ILike: lambda self, e: self.binary(e, "ILIKE"),
            exp.MD5: rename_func("HASH"),
            exp.StrPosition: rename_func("INSTR"),
            exp.TimeToStr: lambda self, e: self.func("TO_CHAR", e.this, self.format_time(e)),
            exp.TsOrDsToDate: lambda self, e: self.func("TO_DATE", e.this, self.format_time(e))
            if e.args.get("format")
            else self.func("DATE", e.this),
            exp.StrToTime: lambda self, e: self.func("TO_TIMESTAMP", e.this, self.format_time(e)),
            exp.TimestampTrunc: timestamptrunc_sql(),
        }

        TYPE_MAPPING = {
            **generator.Generator.TYPE_MAPPING,
            exp.DataType.Type.BOOLEAN: "BOOLEAN",
            exp.DataType.Type.TINYINT: "TINYINT",
            exp.DataType.Type.SMALLINT: "SMALLINT",
            exp.DataType.Type.INT: "INTEGER",
            exp.DataType.Type.BIGINT: "BIGINT",
            exp.DataType.Type.DECIMAL: "DECIMAL",
            exp.DataType.Type.DOUBLE: "DOUBLE PRECISION",
            exp.DataType.Type.FLOAT: "FLOAT",
            # Vertica-specific data types
            exp.DataType.Type.UUID: "UUID",
            exp.DataType.Type.GEOGRAPHY: "GEOGRAPHY",
            exp.DataType.Type.GEOMETRY: "GEOMETRY",
            exp.DataType.Type.VARCHAR: "VARCHAR",
            exp.DataType.Type.CHAR: "CHAR",
            exp.DataType.Type.TEXT: "LONG VARCHAR",
            exp.DataType.Type.BINARY: "BINARY",
            exp.DataType.Type.VARBINARY: "VARBINARY",
            exp.DataType.Type.DATE: "DATE",
            exp.DataType.Type.DATETIME: "TIMESTAMP",
            exp.DataType.Type.TIME: "TIME",
            exp.DataType.Type.TIMESTAMP: "TIMESTAMP",
            exp.DataType.Type.TIMESTAMPTZ: "TIMESTAMPTZ",
            exp.DataType.Type.INTERVAL: "INTERVAL",
            exp.DataType.Type.UUID: "UUID",
            exp.DataType.Type.ARRAY: "ARRAY",
            exp.DataType.Type.JSON: "LONG VARCHAR",  # Vertica stores JSON as text
        }

        # Vertica-specific reserved keywords
        RESERVED_KEYWORDS = {
            "abort", "absolute", "access", "action", "active", "add", "admin", "after",
            "aggregate", "all", "allocate", "alter", "always", "analyse", "analyze",
            "and", "any", "are", "array", "as", "asc", "assertion", "assignment",
            "asymmetric", "at", "authorization", "backward", "before", "begin",
            "between", "bigint", "binary", "bit", "boolean", "both", "by", "cache",
            "called", "cascade", "cascaded", "case", "cast", "catalog", "chain",
            "char", "character", "characteristics", "check", "checkpoint", "class",
            "close", "cluster", "coalesce", "collate", "collation", "column",
            "comment", "comments", "commit", "committed", "constraint", "constraints",
            "conversion", "convert", "copy", "corresponding", "create", "cross",
            "csv", "current", "current_catalog", "current_date", "current_role",
            "current_schema", "current_time", "current_timestamp", "current_user",
            "cursor", "cycle", "data", "database", "day", "deallocate", "dec",
            "decimal", "declare", "default", "defaults", "deferrable", "deferred",
            "definer", "delete", "delimiter", "delimiters", "desc", "dictionary",
            "disable", "discard", "distinct", "do", "domain", "double", "drop",
            "each", "else", "enable", "encoding", "encrypted", "end", "enum",
            "escape", "event", "except", "exception", "exclude", "excluding",
            "exclusive", "execute", "exists", "explain", "external", "extract",
            "false", "family", "fetch", "filter", "first", "float", "following",
            "for", "force", "foreign", "forward", "freeze", "from", "full",
            "function", "functions", "global", "grant", "granted", "greatest",
            "group", "grouping", "handler", "having", "header", "hold", "hour",
            "identity", "if", "ilike", "immediate", "immutable", "implicit",
            "in", "including", "increment", "index", "indexes", "inherit",
            "inherits", "initially", "inline", "inner", "inout", "input",
            "insensitive", "insert", "instead", "int", "integer", "intersect",
            "interval", "into", "invoker", "is", "isnull", "isolation", "join",
            "key", "label", "language", "large", "last", "lc_collate", "lc_ctype",
            "leading", "least", "left", "level", "like", "limit", "listen",
            "load", "local", "localtime", "localtimestamp", "location", "lock",
            "login", "mapping", "match", "maxvalue", "minute", "minvalue", "mode",
            "month", "move", "name", "names", "national", "natural", "nchar",
            "new", "next", "no", "nocreatedb", "nocreaterole", "nocreateuser",
            "noinherit", "nologin", "none", "nosuperuser", "not", "nothing",
            "notify", "notnull", "nowait", "null", "nullif", "nulls", "numeric",
            "object", "of", "off", "offset", "oids", "old", "on", "only",
            "operator", "option", "options", "or", "order", "ordinality", "out",
            "outer", "over", "overlaps", "overlay", "owned", "owner", "partial",
            "partition", "password", "placing", "plans", "position", "preceding",
            "precision", "prepare", "prepared", "preserve", "primary", "prior",
            "privileges", "procedural", "procedure", "program", "quote", "range",
            "read", "real", "recheck", "recursive", "ref", "references",
            "reindex", "relative", "release", "rename", "repeatable", "replace",
            "replica", "reset", "restart", "restrict", "returns", "revoke",
            "right", "role", "rollback", "rollup", "row", "rows", "rule",
            "savepoint", "schema", "scroll", "search", "second", "security",
            "select", "sequence", "serializable", "session", "session_user",
            "set", "setof", "share", "show", "similar", "simple", "smallint",
            "snapshot", "some", "stable", "standalone", "start", "statement",
            "statistics", "stdin", "stdout", "storage", "strict", "strip",
            "substring", "superuser", "symmetric", "sysid", "system", "table",
            "tables", "tablespace", "temp", "template", "temporary", "then",
            "time", "timestamp", "to", "trailing", "transaction", "treat",
            "trigger", "trim", "true", "truncate", "trusted", "type", "unbounded",
            "uncommitted", "unencrypted", "union", "unique", "unknown", "unlisten",
            "until", "update", "user", "using", "vacuum", "valid", "validate",
            "validator", "value", "values", "varchar", "varying", "verbose",
            "version", "view", "volatile", "when", "where", "whitespace",
            "window", "with", "without", "work", "write", "xml", "xmlattributes",
            "xmlconcat", "xmlelement", "xmlexists", "xmlforest", "xmlparse",
            "xmlpi", "xmlroot", "xmlserialize", "year", "yes", "zone",
        }

        def datatype_sql(self, expression: exp.DataType) -> str:
            """Generate Vertica-specific data type SQL"""
            if expression.is_type("LONG VARCHAR"):
                return "LONG VARCHAR"
            elif expression.is_type("LONG VARBINARY"):
                return "LONG VARBINARY"
            elif expression.is_type("TIMESTAMPTZ"):
                return "TIMESTAMPTZ"
            elif expression.is_type("UUID"):
                return "UUID"
            
            return super().datatype_sql(expression)

        def select_sql(self, expression: exp.Select) -> str:
            """Override to handle Vertica-specific SELECT syntax"""
            # Handle TIMESERIES clause if present
            timeseries = expression.args.get("timeseries")
            if timeseries:
                self.unsupported("TIMESERIES clause is Vertica-specific")
            
            return super().select_sql(expression)
        
        def create_sql(self, expression: exp.Create) -> str:
            """Override to handle Vertica-specific CREATE syntax for projections"""
            kind = expression.args.get("kind")
            if kind and kind.upper() == "PROJECTION":
                # Handle CREATE PROJECTION syntax
                this = self.sql(expression, "this")
                as_clause = self.sql(expression, "expression")
                
                # Build projection-specific clauses
                projection_sql = f"CREATE PROJECTION {this}"
                if as_clause:
                    projection_sql += f" AS {as_clause}"
                
                # Handle segmentation
                properties = expression.args.get("properties")
                if properties:
                    for prop in properties.expressions:
                        if hasattr(prop, 'this') and str(prop.this).upper() == "SEGMENTED":
                            segmented_by = self.sql(prop, "expression")
                            if segmented_by:
                                projection_sql += f" SEGMENTED BY {segmented_by}"
                        elif hasattr(prop, 'this') and str(prop.this).upper() == "UNSEGMENTED":
                            projection_sql += " UNSEGMENTED"
                
                return projection_sql
            
            return super().create_sql(expression)
        
        def partition_sql(self, expression: exp.Partition) -> str:
            """Handle Vertica partitioning syntax"""
            return f"PARTITION BY {self.sql(expression, 'this')}"