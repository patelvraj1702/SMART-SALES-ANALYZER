package com.smartsales

import org.apache.spark.sql.{SparkSession, DataFrame, functions => F}
import org.apache.spark.sql.types._
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import java.io.{File, FileWriter}
import scala.util.{Try, Success, Failure}

/**
 * Smart Sales Analyzer — Spark Analytics Engine
 *
 * Usage:
 *   spark-submit --class com.smartsales.SalesAnalyzer \
 *     smart-sales-analyzer-spark-assembly-1.0.0.jar \
 *     <input_csv_path> <output_json_path> <job_id>
 *
 * Input CSV must have columns (all lowercase, after Python normalisation):
 *   product_name, quantity, unit_price, revenue, transaction_date,
 *   category (optional), order_id (optional)
 *
 * Output JSON schema:
 *   { job_id, status, summary, products, monthly, day_of_month, error }
 */
object SalesAnalyzer {

  val mapper: ObjectMapper = {
    val m = new ObjectMapper()
    m.registerModule(DefaultScalaModule)
    m
  }

  def main(args: Array[String]): Unit = {
    if (args.length < 3) {
      System.err.println("Usage: SalesAnalyzer <input_csv> <output_json> <job_id>")
      System.exit(1)
    }

    val inputCsv   = args(0)
    val outputJson = args(1)
    val jobId      = args(2)

    val spark = SparkSession.builder()
      .appName(s"SmartSalesAnalyzer-$jobId")
      .master("local[*]")
      .config("spark.sql.shuffle.partitions", "4")
      .config("spark.ui.enabled", "false")
      .config("spark.driver.memory", "1g")
      .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    val result: Map[String, Any] = Try {
      runAnalytics(spark, inputCsv, jobId)
    } match {
      case Success(r) => r
      case Failure(ex) =>
        Map(
          "job_id"  -> jobId,
          "status"  -> "error",
          "error"   -> ex.getMessage,
          "summary" -> Map.empty[String, Any],
          "products" -> List.empty,
          "monthly"  -> List.empty,
          "day_of_month" -> List.empty
        )
    }

    spark.stop()

    // Write output JSON
    val out = new FileWriter(new File(outputJson))
    out.write(mapper.writeValueAsString(result))
    out.close()
  }

  def runAnalytics(spark: SparkSession, inputCsv: String, jobId: String): Map[String, Any] = {
    import spark.implicits._

    // ── 1. Load CSV ──────────────────────────────────────────────────────────
    val rawDf = spark.read
      .option("header", "true")
      .option("inferSchema", "false")
      .option("mode", "PERMISSIVE")
      .csv(inputCsv)

    if (rawDf.count() == 0) {
      return Map(
        "job_id"  -> jobId,
        "status"  -> "success",
        "summary" -> Map("total_revenue" -> 0.0, "total_units" -> 0L,
                         "product_count" -> 0L, "order_count" -> 0L),
        "products"     -> List.empty,
        "monthly"      -> List.empty,
        "day_of_month" -> List.empty
      )
    }

    // ── 2. Ensure columns exist and compute revenue if needed ────────────────
    val colNames = rawDf.columns.map(_.toLowerCase)
    var stepDf = rawDf

    if (!colNames.contains("product_name")) {
      stepDf = stepDf.withColumn("product_name", F.lit(null).cast(StringType))
    }
    if (!colNames.contains("quantity")) {
      stepDf = stepDf.withColumn("quantity", F.lit(null).cast(StringType))
    }
    if (!colNames.contains("unit_price")) {
      stepDf = stepDf.withColumn("unit_price", F.lit(null).cast(StringType))
    }
    if (!colNames.contains("transaction_date")) {
      stepDf = stepDf.withColumn("transaction_date", F.lit(null).cast(StringType))
    }
    if (!colNames.contains("transaction_datetime")) {
      stepDf = stepDf.withColumn("transaction_datetime", F.lit(null).cast(StringType))
    }

    // Revenue column resolution
    val dfWithRevenue = if (colNames.contains("revenue")) {
      stepDf
        .withColumn("quantity",   F.col("quantity").cast(DoubleType))
        .withColumn("unit_price", F.col("unit_price").cast(DoubleType))
        .withColumn("revenue",
          F.when(F.col("revenue").isNotNull && F.trim(F.col("revenue")) =!= "", F.col("revenue").cast(DoubleType))
           .when(F.col("quantity").isNotNull && F.col("unit_price").isNotNull, F.col("quantity") * F.col("unit_price"))
           .otherwise(null)
        )
    } else {
      stepDf
        .withColumn("quantity",   F.col("quantity").cast(DoubleType))
        .withColumn("unit_price", F.col("unit_price").cast(DoubleType))
        .withColumn("revenue",
          F.when(F.col("quantity").isNotNull && F.col("unit_price").isNotNull, F.col("quantity") * F.col("unit_price"))
           .otherwise(null)
        )
    }

    val df = dfWithRevenue
      .withColumn("transaction_date",
        F.coalesce(
          F.to_date(F.col("transaction_date"), "yyyy-MM-dd"),
          F.to_date(F.col("transaction_datetime"), "yyyy-MM-dd'T'HH:mm:ss"),
          F.to_date(F.col("transaction_date"), "yyyy-MM-dd HH:mm:ss"),
          F.to_date(F.col("transaction_date"), "yyyy/MM/dd"),
          F.to_date(F.col("transaction_date"), "dd-MM-yyyy"),
          F.to_date(F.col("transaction_date"), "dd/MM/yyyy"),
          F.to_date(F.col("transaction_date"), "MM/dd/yyyy"),
          F.to_date(F.col("transaction_date"))
        )
      )
      .filter(F.col("product_name").isNotNull && F.trim(F.col("product_name")) =!= "")
      .filter(F.col("quantity").isNotNull && F.col("quantity") > 0)
      .filter(F.col("revenue").isNotNull && F.col("revenue") > 0)
      .cache()

    val totalRows = df.count()

    // ── 3. Summary metrics ───────────────────────────────────────────────────
    val summaryRow = df.agg(
      F.sum("revenue").alias("total_revenue"),
      F.sum("quantity").alias("total_units"),
      F.countDistinct("product_name").alias("product_count")
    ).first()

    val totalRevenue  = Option(summaryRow.getAs[Double]("total_revenue")).getOrElse(0.0)
    val totalUnits    = Option(summaryRow.getAs[Double]("total_units")).map(_.toLong).getOrElse(0L)
    val productCount  = Option(summaryRow.getAs[Long]("product_count")).getOrElse(0L)

    // Order count — only meaningful when order_id column is non-null/non-empty
    val hasOrderId = df.columns.contains("order_id")
    val orderCount: Long = if (hasOrderId) {
      df.filter(F.col("order_id").isNotNull && F.trim(F.col("order_id")) =!= "")
        .select(F.countDistinct("order_id"))
        .first().getLong(0)
    } else 0L

    val summary = Map(
      "total_revenue"   -> roundTo2(totalRevenue),
      "total_units"     -> totalUnits,
      "product_count"   -> productCount,
      "order_count"     -> orderCount,
      "row_count"       -> totalRows
    )

    // ── 4. Product analytics ─────────────────────────────────────────────────
    val productBase = df.groupBy("product_name")
      .agg(
        F.sum("revenue").alias("total_revenue"),
        F.sum("quantity").alias("total_quantity")
      )

    // optional category join
    val productDf: DataFrame = if (df.columns.contains("category")) {
      val catMap = df
        .filter(F.col("category").isNotNull)
        .groupBy("product_name")
        .agg(F.first("category").alias("category"))
      productBase.join(catMap, Seq("product_name"), "left")
    } else {
      productBase.withColumn("category", F.lit(null).cast(StringType))
    }

    val productsRows = productDf
      .orderBy(F.desc("total_revenue"))
      .collect()
      .zipWithIndex
      .map { case (row, idx) =>
        Map(
          "rank"           -> (idx + 1),
          "product_name"   -> row.getAs[String]("product_name"),
          "total_revenue"  -> roundTo2(row.getAs[Double]("total_revenue")),
          "total_quantity" -> row.getAs[Double]("total_quantity").toLong,
          "category"       -> Option(row.getAs[String]("category")).getOrElse("")
        )
      }.toList

    // ── 5. Monthly analytics ──────────────────────────────────────────────────
    val monthlyRows = df
      .filter(F.col("transaction_date").isNotNull)
      .withColumn("month", F.date_format(F.col("transaction_date"), "yyyy-MM"))
      .groupBy("month")
      .agg(
        F.sum("revenue").alias("revenue"),
        F.sum("quantity").alias("units_sold")
      )
      .orderBy("month")
      .collect()
      .map { row =>
        Map(
          "month"      -> row.getAs[String]("month"),
          "revenue"    -> roundTo2(row.getAs[Double]("revenue")),
          "units_sold" -> row.getAs[Double]("units_sold").toLong
        )
      }.toList

    // ── 6. Day-of-month analytics ─────────────────────────────────────────────
    val dayOfMonthRows = df
      .filter(F.col("transaction_date").isNotNull)
      .withColumn("day", F.dayofmonth(F.col("transaction_date")))
      .groupBy("day")
      .agg(
        F.sum("revenue").alias("revenue"),
        F.sum("quantity").alias("units_sold")
      )
      .orderBy("day")
      .collect()
      .map { row =>
        Map(
          "day"        -> row.getAs[Int]("day"),
          "revenue"    -> roundTo2(row.getAs[Double]("revenue")),
          "units_sold" -> row.getAs[Double]("units_sold").toLong
        )
      }.toList

    df.unpersist()

    Map(
      "job_id"       -> jobId,
      "status"       -> "success",
      "summary"      -> summary,
      "products"     -> productsRows,
      "monthly"      -> monthlyRows,
      "day_of_month" -> dayOfMonthRows
    )
  }

  private def roundTo2(v: Double): Double =
    BigDecimal(v).setScale(2, BigDecimal.RoundingMode.HALF_UP).toDouble
}
