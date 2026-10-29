import argparse


class LoaderArgumentParser:
    @staticmethod
    def parse_args(description: str) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("--catalog_name", type=str, required=False, help="Catalog name.")
        parser.add_argument(
            "--technical_catalog_name",
            type=str,
            required=False,
            help="Technical catalog name.",
        )
        parser.add_argument("--bronze_schema_name", type=str, required=False, help="Bronze schema name.")
        parser.add_argument("--silver_schema_name", type=str, required=False, help="Silver schema name.")
        parser.add_argument("--gold_schema_name", type=str, required=False, help="Gold schema name.")
        parser.add_argument(
            "--source_data_schema_name",
            type=str,
            required=False,
            help="Source data schema name.",
        )
        return parser.parse_args()
