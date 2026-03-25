from sqlglot import exp, generator, tokens
from sqlglot.dialects.dialect import Dialect, NormalizationStrategy


class Vertica(Dialect):
    NORMALIZATION_STRATEGY = NormalizationStrategy.CASE_INSENSITIVE

    class Tokenizer(tokens.Tokenizer):
        QUOTES = ["'", '"']
        IDENTIFIERS = ["`"]

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
        }

    class Generator(generator.Generator):
        TYPE_MAPPING = {
            **generator.Generator.TYPE_MAPPING,
            exp.DataType.Type.INTERVAL: "BIGINT",
        }
