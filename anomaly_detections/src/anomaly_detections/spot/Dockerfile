FROM rdsea/pyflink_base:latest

# Install pip dependencies
RUN pip install "apache-flink==1.20"

RUN wget -P /opt/flink/usrlib https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.4.0-1.20/flink-sql-connector-kafka-3.4.0-1.20.jar

# Add Kafka client jar (adjust version as needed)
RUN wget -P /opt/flink/usrlib https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.6.0/kafka-clients-3.6.0.jar

ADD --chown=flink:flink flink_anomaly_detections_test.py /opt/flink/usrlib/pyflink_main.py
