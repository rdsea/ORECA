from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.table import StreamTableEnvironment


def log_processing():
    kafka_servers = "redpanda-0.redpanda.redpanda.svc.cluster.local:9093"
    source_topic = "prometheus-metric"
    kafka_consumer_group_id = "test"

    s_env = StreamExecutionEnvironment.get_execution_environment()
    s_env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
    t_env = StreamTableEnvironment.create(stream_execution_environment=s_env)

    t_env.get_config().get_configuration().set_boolean(
        "python.fn-execution.memory.managed", True
    )

    source_ddl = f"""
    CREATE TABLE prometheus_metric (
        `name` STRING,
        `timestamp` TIMESTAMP(3),
        `metric_value` STRING,
        `labels` ROW<
            __name__ STRING,
            container STRING,
            endpoint STRING,
            id STRING,
            image STRING,
            instance STRING,
            job STRING,
            metrics_path STRING,
            name STRING,
            namespace STRING,
            node STRING,
            pod STRING,
            prometheus STRING,
            prometheus_replica STRING,
            service STRING
        >,
        WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = '{source_topic}',
        'properties.bootstrap.servers' = '{kafka_servers}',
        'properties.group.id' = '{kafka_consumer_group_id}',
        'scan.startup.mode' = 'latest-offset',
        'format' = 'json',
        'json.fail-on-missing-field' = 'false',
        'json.ignore-parse-errors' = 'true',

        -- SECURITY
        'properties.security.protocol' = 'SASL_SSL',
        'properties.sasl.mechanism' = 'PLAIN',
        'properties.sasl.jaas.config' = 'org.apache.kafka.common.security.plain.PlainLoginModule required username="alice" password="redpanda";',
        'properties.ssl.truststore.location' = '/etc/tls/truststore/truststore.jks',
        'properties.ssl.truststore.password' = 'changeit'
    );
    """

    rate_per_pod_sql = """
    CREATE VIEW pod_cpu_usage_rate AS
    SELECT
        COUNT(*) as number_of_metric,
        labels.pod AS pod,
        labels.namespace AS namespace
    FROM prometheus_metric
    GROUP BY
        labels.pod,
        labels.namespace
    """

    t_env.execute_sql(source_ddl)

    t_env.execute_sql(rate_per_pod_sql)
    result_table = t_env.sql_query("SELECT * FROM pod_cpu_usage_rate")
    result_table.execute().print()


if __name__ == "__main__":
    log_processing()
