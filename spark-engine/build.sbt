name := "smart-sales-analyzer-spark"
version := "1.0.0"
scalaVersion := "2.12.18"

// Spark 3.5.3 with Scala 2.12
val sparkVersion = "3.5.3"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-sql"  % sparkVersion % "provided",
  "com.fasterxml.jackson.core" % "jackson-databind" % "2.15.4",
  "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.15.4"
)

// Fat JAR: exclude scala and spark libs (they are provided by spark-submit)
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case "reference.conf"               => MergeStrategy.concat
  case _                              => MergeStrategy.first
}

assembly / mainClass := Some("com.smartsales.SalesAnalyzer")
