"""Transform Kamernet source data into the silver layer."""

from databricks.sdk.runtime import spark
from pyspark.sql import functions as F

from rent_analysis.utils.loader_argument_parser import LoaderArgumentParser
from rent_analysis.utils.utils import Utils


class SilverKamernetLoader:
    """Clean and type Kamernet data for downstream analysis."""

    @staticmethod
    def execute_task():
        """Normalize Kamernet records and overwrite the silver table."""
        args = LoaderArgumentParser.parse_args(description="Load Kamernet data into the silver layer.")

        df_bronze = spark.read.table(f"{args.catalog_name}.{args.bronze_schema_name}.kamernet")

        df_clean_amounts = df_bronze.withColumns(
            {
                "rent_in_eur": Utils.extract_euro_amount(F.col("rent")),
                "deposit_in_eur": Utils.extract_euro_amount(F.col("deposit")),
                "registration_cost_in_eur": Utils.extract_euro_amount(F.col("registrationCost")),
                "additional_costs_raw_in_eur": Utils.extract_euro_amount(F.col("additionalCostsRaw")),
                "area_in_sqm": F.regexp_replace(F.col("areaSqm"), "m2", ""),
            }
        )

        df_typecasted = df_clean_amounts.withColumns(
            {
                "longitude": F.col("longitude").cast("float"),
                "latitude": F.col("latitude").cast("float"),
                "area_in_sqm": F.col("area_in_sqm").cast("integer"),
                "is_room_active": F.col("isRoomActive").try_cast("boolean"),
            }
        )

        df_non_values_filled = df_typecasted.withColumns(
            {
                "deposit_in_eur": F.when(F.col("deposit_in_eur").isNull(), 0).otherwise(F.col("deposit_in_eur")),
                "registration_cost_in_eur": F.when(F.col("registration_cost_in_eur").isNull(), 0).otherwise(
                    F.col("registration_cost_in_eur")
                ),
                "additional_costs_raw_in_eur": F.when(F.col("additional_costs_raw_in_eur").isNull(), 0).otherwise(
                    F.col("additional_costs_raw_in_eur")
                ),
            }
        )

        df_selected = df_non_values_filled.select(
            F.col("additional_costs_raw_in_eur"),
            F.col("area_in_sqm"),
            F.col("availability"),
            F.col("city"),
            F.col("deposit_in_eur"),
            F.col("descriptionTranslated").alias("description_translated"),
            F.col("energyLabel").alias("energy_label"),
            F.col("furnish"),
            F.col("gender"),
            F.col("internet"),
            F.col("is_room_active"),
            F.col("kitchen"),
            F.col("living"),
            F.col("latitude"),
            F.col("longitude"),
            F.col("matchCapacity").alias("match_capacity"),
            F.col("pageDescription").alias("page_description"),
            F.col("pageTitle").alias("page_title"),
            F.col("pets"),
            F.col("postalCode").alias("postal_code"),
            F.col("propertyType").alias("property_type"),
            F.col("registration_cost_in_eur"),
            F.col("rent_in_eur"),
            F.col("roommates"),
            F.col("shower"),
            F.col("smokingInside").alias("smoking_inside"),
            F.col("toilet"),
            F.col("source"),
        )

        df_selected.write.mode("overwrite").saveAsTable(f"{args.catalog_name}.{args.silver_schema_name}.kamernet")
