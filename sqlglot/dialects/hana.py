from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.tokens import Tokenizer, TokenType


class HANA(Dialect):
    class Tokenizer(Tokenizer):
        KEYWORDS = {
            **Tokenizer.KEYWORDS,
            "NVARCHAR": TokenType.VARCHAR,
            "ALPHANUM": TokenType.VARBINARY,
        }

    class Generator(Dialect.Generator):
        TRANSFORMS = {
            **Dialect.Generator.TRANSFORMS,
            # Add HANA-specific transformations here
        }
