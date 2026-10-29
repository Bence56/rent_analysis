import sys

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser


def test_all_arguments_are_optional(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["loader"])

    args = LoaderArgumentParser.parse_args("Test loader")

    assert vars(args) == {
        "catalog_name": None,
        "technical_catalog_name": None,
        "bronze_schema_name": None,
        "silver_schema_name": None,
        "gold_schema_name": None,
        "source_data_schema_name": None,
    }


def test_parses_all_loader_arguments(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "loader",
            "--catalog_name",
            "rent_analysis",
            "--technical_catalog_name",
            "technical",
            "--bronze_schema_name",
            "bronze",
            "--silver_schema_name",
            "silver",
            "--gold_schema_name",
            "gold",
            "--source_data_schema_name",
            "source_data",
        ],
    )

    args = LoaderArgumentParser.parse_args("Test loader")

    assert vars(args) == {
        "catalog_name": "rent_analysis",
        "technical_catalog_name": "technical",
        "bronze_schema_name": "bronze",
        "silver_schema_name": "silver",
        "gold_schema_name": "gold",
        "source_data_schema_name": "source_data",
    }
