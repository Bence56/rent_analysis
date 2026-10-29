"""Build property price statistics by district in the gold layer."""

from databricks.sdk.runtime import spark
from pyspark.sql import functions as F

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser
from rent_analysis.utils.utils import Utils


class GoldStatisticsPerDistrictLoader:
    """Calculate property price statistics grouped by district."""

    @staticmethod
    def execute_task():
        """Aggregate silver properties by postal code and overwrite the gold table."""
        args = LoaderArgumentParser.parse_args(description="Load property statistics per district into the gold layer.")

        df_joinned = Utils.load_silver_properties(
            spark,
            args.catalog_name,
            args.silver_schema_name,
        )

        df_stats = (
            df_joinned.groupBy("postal_code")
            .agg(
                F.min("price").alias("min_price"),
                F.max("price").alias("max_price"),
                F.avg("price").alias("avg_price"),
                F.expr("percentile(price, 0.25)").alias("p25_price"),
                F.expr("percentile(price, 0.50)").alias("median_price"),
                F.expr("percentile(price, 0.75)").alias("p75_price"),
                F.count("*").alias(
                    "properties_in_district"
                ),  # optional: group size helps judge how reliable the stats are
            )
            .orderBy("postal_code")
        )

        df_stats.write.mode("overwrite").saveAsTable(
            f"{args.catalog_name}.{args.gold_schema_name}.property_statistics_per_district"
        )
