"""Shared Spark transformations for property data."""

from pyspark.sql import SparkSession, functions as F
from pyspark.sql import Column, DataFrame


class Utils:
    """Provide shared transformations for Spark property data."""

    @staticmethod
    def load_silver_properties(spark: SparkSession, catalog_name: str, silver_schema_name: str) -> DataFrame:
        """Load and align Airbnb and Kamernet property records from the silver layer."""
        df_airbnb = spark.read.table(f"{catalog_name}.{silver_schema_name}.airbnb")
        df_airbnb = df_airbnb.select(
            F.col("zipcode").alias("postal_code"),
            F.col("latitude"),
            F.col("longitude"),
            F.col("room_type"),
            F.col("price"),
            F.col("source"),
        )

        df_kamernet = spark.read.table(f"{catalog_name}.{silver_schema_name}.kamernet")
        df_kamernet = df_kamernet.select(
            F.col("postal_code"),
            F.col("latitude"),
            F.col("longitude"),
            F.col("property_type").alias("room_type"),
            F.col("rent_in_eur").alias("price"),
            F.col("source"),
        )

        return df_airbnb.unionAll(df_kamernet)

    @staticmethod
    def clean_zipcode(df: DataFrame) -> DataFrame:
        """Normalize postal codes by removing spaces and uppercasing letters."""
        return df.withColumn(
            "zipcode",
            F.upper(
                F.regexp_replace(
                    F.col("zipcode"),
                    r"^(\d{4})\s*([A-Za-z]{2})?$",
                    r"$1$2",
                )
            ),
        )

    @staticmethod
    def fill_with_median(df: DataFrame, column_name: str = "review_scores_value") -> DataFrame:
        """Fill null values in a column with its approximate median."""
        median_row = df.select(F.percentile_approx(F.col(column_name), 0.5).alias("median")).first()
        if median_row is None:
            return df
        median_value = median_row["median"]

        return df.fillna({column_name: median_value})

    @staticmethod
    def extract_euro_amount(col: Column) -> Column:
        """Return the integer after '€ ' in a string, or null if there is none."""
        amount = F.regexp_extract(col, r"€\s*(\d+)", 1)
        return F.when(amount != "", amount.cast("int"))
