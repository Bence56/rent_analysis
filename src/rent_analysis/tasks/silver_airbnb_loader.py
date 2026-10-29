"""Transform Airbnb source data into the silver layer."""

from databricks.sdk.runtime import spark
from pyspark.sql import functions as F

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser
from rent_analysis.utils.utils import Utils


class SilverAirbnbLoader:
    """Clean and type Airbnb data for downstream analysis."""

    @staticmethod
    def execute_task():
        """Clean Airbnb records and overwrite the silver table."""
        args = LoaderArgumentParser.parse_args(description="Load Airbnb data into the silver layer.")

        df_bronze = spark.read.table(f"{args.catalog_name}.{args.bronze_schema_name}.airbnb")

        df_correct_types = df_bronze.withColumns(
            {
                "price": F.col("price").cast("int"),
                "review_scores_value": F.col("review_scores_value").cast("double"),
                "accommodates": F.col("accommodates").cast("int"),
                "bedrooms": F.col("bedrooms").cast("double"),
                "latitude": F.col("latitude").cast("float"),
                "longitude": F.col("longitude").cast("float"),
                "source": F.lit("airbnb"),
            }
        )

        df_filtered_outlier = df_correct_types.filter(F.col("price") < 9000)

        df_clean_zipcode = Utils.clean_zipcode(df_filtered_outlier)
        df_review_scores_filled = Utils.fill_with_median(df_clean_zipcode)

        df_review_scores_filled.write.mode("overwrite").saveAsTable(
            f"{args.catalog_name}.{args.silver_schema_name}.airbnb"
        )
