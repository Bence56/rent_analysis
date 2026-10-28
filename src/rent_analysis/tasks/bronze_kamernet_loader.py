import argparse

from databricks.sdk.runtime import spark


class BronzeKamernetLoader:

    @staticmethod
    def execute_task():
        argument_parser = argparse.ArgumentParser(description="Load Kamernet data into the bronze layer.")
        argument_parser.add_argument("--catalog_name", type=str, required=True, help="Catalog name.")
        argument_parser.add_argument("--technical_catalog_name", type=str, required=True, help="Technical catalog name.")
        argument_parser.add_argument("--bronze_schema_name", type=str, required=True, help="Bronze schema name.")
        argument_parser.add_argument("--source_data_schema_name", type=str, required=True, help="Source data schema name.")

        args = argument_parser.parse_args()
        df = spark.read.json(f"/Volumes/{args.technical_catalog_name}/{args.source_data_schema_name}/kamernet/rentals.json")

        df.write.mode("overwrite").saveAsTable(f"{args.catalog_name}.{args.bronze_schema_name}.kamernet")
