"""Build annual and five-year property revenue data in the gold layer."""

from databricks.sdk.runtime import spark
from pyspark.sql import functions as F

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser
from rent_analysis.utils.utils import Utils


class GoldRevenuePerPropertyLoader:
    """Calculate revenue estimates for properties."""

    @staticmethod
    def execute_task():
        """Load silver properties, calculate revenue, and overwrite the gold table."""
        args = LoaderArgumentParser.parse_args(description="Load revenue per property into the gold layer.")

        df_joinned = Utils.load_silver_properties(
            spark,
            args.catalog_name,
            args.silver_schema_name,
        )

        df_joinned = df_joinned.withColumns(
            {
                "revenue_per_year": F.col("price") * 12,
                "revenue_per_5_years": F.col("price") * 12 * 5,
            }
        )

        df_joinned.write.mode("overwrite").saveAsTable(
            f"{args.catalog_name}.{args.gold_schema_name}.revenue_per_property"
        )
