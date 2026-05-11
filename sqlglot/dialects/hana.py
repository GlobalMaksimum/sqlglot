from sqlglot import exp, generator
from sqlglot.dialects.dialect import Dialect
from sqlglot.tokens import Tokenizer, TokenType


class HANA(Dialect):
    class Tokenizer(Tokenizer):
        KEYWORDS = {
            **Tokenizer.KEYWORDS,
            "NVARCHAR": TokenType.VARCHAR,
            "ALPHANUM": TokenType.VARBINARY,
        }

    class Generator(generator.Generator):
        TRANSFORMS = {
            **generator.Generator.TRANSFORMS,
            # Add HANA-specific transformations here
        }
