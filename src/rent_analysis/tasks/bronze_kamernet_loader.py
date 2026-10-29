"""Load Kamernet source data into the bronze layer."""

from databricks.sdk.runtime import spark

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser


class BronzeKamernetLoader:
    """Load raw Kamernet data into the bronze table."""

    @staticmethod
    def execute_task():
        """Read the Kamernet JSON and overwrite its bronze table."""
        args = LoaderArgumentParser.parse_args(description="Load Kamernet data into the bronze layer.")
        df = spark.read.json(
            f"/Volumes/{args.technical_catalog_name}/{args.source_data_schema_name}/kamernet/rentals.json"
        )

        df.write.mode("overwrite").saveAsTable(f"{args.catalog_name}.{args.bronze_schema_name}.kamernet")
