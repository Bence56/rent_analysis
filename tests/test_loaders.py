import sys
from argparse import Namespace
from types import ModuleType
from unittest.mock import MagicMock

import pytest

runtime_stub = ModuleType("databricks.sdk.runtime")
runtime_stub.spark = MagicMock()
sys.modules["databricks.sdk.runtime"] = runtime_stub

from rent_analysis.tasks import (
    bronze_airbnb_loader,
    bronze_kamernet_loader,
    gold_revenue_loader,
    gold_statistics_per_district,
    silver_airbnb_loader,
    silver_kamernet_loader,
)


class ColumnRef:
    def __init__(self, name):
        self.name = name

    def cast(self, data_type):
        return (self.name, data_type)

    def alias(self, name):
        return (self.name, name)

    def try_cast(self, data_type):
        return (self.name, data_type)

    def isNull(self):
        return (self.name, "isNull")


@pytest.fixture
def loader_args():
    return Namespace(
        catalog_name="test_catalog",
        technical_catalog_name="test_technical",
        bronze_schema_name="bronze_test",
        silver_schema_name="silver_test",
        gold_schema_name="gold_test",
        source_data_schema_name="source_test",
    )


@pytest.mark.parametrize(
    ("module", "loader", "description", "reader_method", "source_path", "table_name"),
    [
        (
            bronze_airbnb_loader,
            bronze_airbnb_loader.BronzeAirbnbLoader,
            "Load Airbnb data into the bronze layer.",
            "csv",
            "/Volumes/test_technical/source_test/airbnb/airbnb.csv",
            "test_catalog.bronze_test.airbnb",
        ),
        (
            bronze_kamernet_loader,
            bronze_kamernet_loader.BronzeKamernetLoader,
            "Load Kamernet data into the bronze layer.",
            "json",
            "/Volumes/test_technical/source_test/kamernet/rentals.json",
            "test_catalog.bronze_test.kamernet",
        ),
    ],
)
def test_bronze_loader_uses_arguments(
    monkeypatch,
    loader_args,
    module,
    loader,
    description,
    reader_method,
    source_path,
    table_name,
):
    spark = MagicMock()
    monkeypatch.setattr(module, "spark", spark)
    parse_args = MagicMock(return_value=loader_args)
    monkeypatch.setattr(module.LoaderArgumentParser, "parse_args", parse_args)
    dataframe = getattr(spark.read, reader_method).return_value

    loader.execute_task()

    parse_args.assert_called_once_with(description=description)
    getattr(spark.read, reader_method).assert_called_once_with(
        source_path,
        **({"header": True} if reader_method == "csv" else {}),
    )
    dataframe.write.mode.assert_called_once_with("overwrite")
    dataframe.write.mode.return_value.saveAsTable.assert_called_once_with(table_name)


def test_silver_airbnb_loader_uses_arguments_and_passes_each_frame(monkeypatch, loader_args):
    module = silver_airbnb_loader
    spark = MagicMock()
    monkeypatch.setattr(module, "spark", spark)
    parse_args = MagicMock(return_value=loader_args)
    monkeypatch.setattr(module.LoaderArgumentParser, "parse_args", parse_args)
    bronze = spark.read.table.return_value
    casted = bronze.withColumns.return_value
    filtered = casted.filter.return_value
    cleaned = MagicMock()
    filled = MagicMock()
    clean_zipcode = MagicMock(return_value=cleaned)
    fill_with_median = MagicMock(return_value=filled)
    monkeypatch.setattr(module.Utils, "clean_zipcode", clean_zipcode)
    monkeypatch.setattr(module.Utils, "fill_with_median", fill_with_median)

    silver_airbnb_loader.SilverAirbnbLoader.execute_task()

    parse_args.assert_called_once_with(description="Load Airbnb data into the silver layer.")
    spark.read.table.assert_called_once_with("test_catalog.bronze_test.airbnb")
    bronze.withColumns.assert_called_once()
    casted.filter.assert_called_once()
    clean_zipcode.assert_called_once_with(filtered)
    fill_with_median.assert_called_once_with(cleaned)
    filled.write.mode.assert_called_once_with("overwrite")
    filled.write.mode.return_value.saveAsTable.assert_called_once_with("test_catalog.silver_test.airbnb")


def test_silver_kamernet_loader_uses_arguments_and_passes_each_frame(monkeypatch, loader_args):
    module = silver_kamernet_loader
    spark = MagicMock()
    monkeypatch.setattr(module, "spark", spark)
    functions = MagicMock()
    functions.col.side_effect = ColumnRef
    monkeypatch.setattr(module, "F", functions)
    parse_args = MagicMock(return_value=loader_args)
    monkeypatch.setattr(module.LoaderArgumentParser, "parse_args", parse_args)
    bronze = spark.read.table.return_value
    cleaned = bronze.withColumns.return_value
    casted = cleaned.withColumns.return_value
    filled = casted.withColumns.return_value
    selected = filled.select.return_value
    extract_amount = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(module.Utils, "extract_euro_amount", extract_amount)

    silver_kamernet_loader.SilverKamernetLoader.execute_task()

    parse_args.assert_called_once_with(description="Load Kamernet data into the silver layer.")
    spark.read.table.assert_called_once_with("test_catalog.bronze_test.kamernet")
    assert bronze.withColumns.call_count == 1
    assert cleaned.withColumns.call_count == 1
    assert casted.withColumns.call_count == 1
    assert [call.args[0].name for call in extract_amount.call_args_list] == [
        "rent",
        "deposit",
        "registrationCost",
        "additionalCostsRaw",
    ]
    filled.select.assert_called_once()
    selected.write.mode.assert_called_once_with("overwrite")
    selected.write.mode.return_value.saveAsTable.assert_called_once_with("test_catalog.silver_test.kamernet")


def test_gold_revenue_loader_uses_arguments_and_writes_calculated_revenue(monkeypatch, loader_args):
    module = gold_revenue_loader
    spark = MagicMock()
    monkeypatch.setattr(module, "spark", spark)
    parse_args = MagicMock(return_value=loader_args)
    monkeypatch.setattr(module.LoaderArgumentParser, "parse_args", parse_args)
    properties = MagicMock()
    load_properties = MagicMock(return_value=properties)
    monkeypatch.setattr(module.Utils, "load_silver_properties", load_properties)
    with_revenue = properties.withColumns.return_value

    gold_revenue_loader.GoldRevenuePerPropertyLoader.execute_task()

    parse_args.assert_called_once_with(description="Load revenue per property into the gold layer.")
    load_properties.assert_called_once_with(spark, "test_catalog", "silver_test")
    properties.withColumns.assert_called_once()
    assert set(properties.withColumns.call_args.args[0]) == {
        "revenue_per_year",
        "revenue_per_5_years",
    }
    with_revenue.write.mode.assert_called_once_with("overwrite")
    with_revenue.write.mode.return_value.saveAsTable.assert_called_once_with(
        "test_catalog.gold_test.revenue_per_property"
    )


def test_gold_statistics_loader_uses_arguments_and_writes_district_statistics(monkeypatch, loader_args):
    module = gold_statistics_per_district
    spark = MagicMock()
    monkeypatch.setattr(module, "spark", spark)
    parse_args = MagicMock(return_value=loader_args)
    monkeypatch.setattr(module.LoaderArgumentParser, "parse_args", parse_args)
    properties = MagicMock()
    load_properties = MagicMock(return_value=properties)
    monkeypatch.setattr(module.Utils, "load_silver_properties", load_properties)
    grouped = properties.groupBy.return_value
    aggregated = grouped.agg.return_value
    ordered = aggregated.orderBy.return_value

    gold_statistics_per_district.GoldStatisticsPerDistrictLoader.execute_task()

    parse_args.assert_called_once_with(
        description="Load property statistics per district into the gold layer."
    )
    load_properties.assert_called_once_with(spark, "test_catalog", "silver_test")
    properties.groupBy.assert_called_once_with("postal_code")
    grouped.agg.assert_called_once()
    aggregated.orderBy.assert_called_once_with("postal_code")
    ordered.write.mode.assert_called_once_with("overwrite")
    ordered.write.mode.return_value.saveAsTable.assert_called_once_with(
        "test_catalog.gold_test.property_statistics_per_district"
    )
