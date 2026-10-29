from types import SimpleNamespace

import rent_analysis.utils.utils as utils_module
from rent_analysis.utils.utils import Utils


class Expression:
    def __init__(self, operation, *arguments):
        self.operation = operation
        self.arguments = arguments

    def alias(self, name):
        return Expression("alias", self, name)

    def cast(self, data_type):
        return Expression("cast", self, data_type)

    def __ne__(self, other):
        return Expression("not_equal", self, other)

    def __eq__(self, other):
        return isinstance(other, Expression) and (
            self.operation,
            self.arguments,
        ) == (
            other.operation,
            other.arguments,
        )

    def __repr__(self):
        return f"Expression({self.operation!r}, {self.arguments!r})"


def make_functions():
    return SimpleNamespace(
        col=lambda name: Expression("col", name),
        upper=lambda value: Expression("upper", value),
        regexp_replace=lambda *args: Expression("regexp_replace", *args),
        percentile_approx=lambda *args: Expression("percentile_approx", *args),
        regexp_extract=lambda *args: Expression("regexp_extract", *args),
        when=lambda *args: Expression("when", *args),
    )


class FakeDataFrame:
    def __init__(self, median=3.0):
        self.median = median
        self.selected = None
        self.with_column = None
        self.filled = None
        self.union_frame = None

    def withColumn(self, name, expression):
        self.with_column = (name, expression)
        return self

    def select(self, *expressions):
        self.selected = expressions
        return self

    def first(self):
        return {"median": self.median}

    def fillna(self, values):
        self.filled = values
        return self

    def unionAll(self, other):
        self.union_frame = other
        return self


def test_clean_zipcode_builds_normalization_expression(monkeypatch):
    monkeypatch.setattr(utils_module, "F", make_functions())
    df = FakeDataFrame()

    result = Utils.clean_zipcode(df)

    expected = Expression(
        "upper",
        Expression(
            "regexp_replace",
            Expression("col", "zipcode"),
            r"^(\d{4})\s*([A-Za-z]{2})?$",
            r"$1$2",
        ),
    )
    assert result is df
    assert df.with_column == ("zipcode", expected)


def test_fill_with_median_replaces_nulls_in_default_column(monkeypatch):
    monkeypatch.setattr(utils_module, "F", make_functions())
    df = FakeDataFrame(median=4.5)

    result = Utils.fill_with_median(df)

    assert result is df
    assert df.selected == (
        Expression(
            "alias",
            Expression(
                "percentile_approx",
                Expression("col", "review_scores_value"),
                0.5,
            ),
            "median",
        ),
    )
    assert df.filled == {"review_scores_value": 4.5}


def test_fill_with_median_supports_a_custom_column(monkeypatch):
    monkeypatch.setattr(utils_module, "F", make_functions())
    df = FakeDataFrame(median=12)

    Utils.fill_with_median(df, "score")

    assert df.filled == {"score": 12}
    assert df.selected[0].arguments[0].arguments[0] == Expression("col", "score")


def test_extract_euro_amount_extracts_integer_or_returns_null(monkeypatch):
    monkeypatch.setattr(utils_module, "F", make_functions())
    column = Expression("col", "rent")

    result = Utils.extract_euro_amount(column)

    amount = Expression("regexp_extract", column, r"€\s*(\d+)", 1)
    assert result == Expression(
        "when",
        Expression("not_equal", amount, ""),
        Expression("cast", amount, "int"),
    )


def test_load_silver_properties_aligns_both_sources(monkeypatch):
    monkeypatch.setattr(utils_module, "F", make_functions())
    airbnb = FakeDataFrame()
    kamernet = FakeDataFrame()

    class Reader:
        def table(self, name):
            return {
                "rent_analysis.silver.airbnb": airbnb,
                "rent_analysis.silver.kamernet": kamernet,
            }[name]

    spark = SimpleNamespace(read=Reader())

    result = Utils.load_silver_properties(spark, "rent_analysis", "silver")

    assert airbnb.selected == (
        Expression("alias", Expression("col", "zipcode"), "postal_code"),
        Expression("col", "latitude"),
        Expression("col", "longitude"),
        Expression("col", "room_type"),
        Expression("col", "price"),
        Expression("col", "source"),
    )
    assert kamernet.selected == (
        Expression("col", "postal_code"),
        Expression("col", "latitude"),
        Expression("col", "longitude"),
        Expression("alias", Expression("col", "property_type"), "room_type"),
        Expression("alias", Expression("col", "rent_in_eur"), "price"),
        Expression("col", "source"),
    )
    assert airbnb.union_frame is kamernet
    assert result is airbnb
