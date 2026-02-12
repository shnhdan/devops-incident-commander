#!/usr/bin/env python3
"""Generate realistic system metrics"""

from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import os


def get_es_client():
    load_dotenv()
    return Elasticsearch(
        os.getenv("ELASTIC_ENDPOINT"),
        basic_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),
        verify_certs=True,
    )


def generate_metrics(count=20000):
    """Generate realistic system metrics with anomalies"""

    services = [
        "api-gateway",
        "payment-service",
        "user-service",
        "auth-service",
        "order-service",
    ]
    metrics = [
        "cpu_usage",
        "memory_usage",
        "request_latency",
        "error_rate",
        "queue_depth",
    ]
    hosts = ["prod-01", "prod-02", "prod-03", "prod-04", "prod-05"]

    docs = []
    now = datetime.utcnow()

    for i in range(count):
        timestamp = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        metric_name = random.choice(metrics)

        # 10% chance of anomaly/spike
        is_anomaly = random.random() < 0.1

        if is_anomaly:
            if metric_name == "cpu_usage":
                value = random.uniform(85, 98)
            elif metric_name == "memory_usage":
                value = random.uniform(85, 95)
            elif metric_name == "request_latency":
                value = random.uniform(2000, 5000)  # milliseconds
            elif metric_name == "error_rate":
                value = random.uniform(5, 15)  # percentage
            elif metric_name == "queue_depth":
                value = random.randint(500, 1000)
        else:
            if metric_name == "cpu_usage":
                value = random.uniform(20, 60)
            elif metric_name == "memory_usage":
                value = random.uniform(40, 70)
            elif metric_name == "request_latency":
                value = random.uniform(50, 200)
            elif metric_name == "error_rate":
                value = random.uniform(0.1, 2)
            elif metric_name == "queue_depth":
                value = random.randint(10, 100)

        doc = {
            "@timestamp": timestamp.isoformat(),
            "service_name": random.choice(services),
            "metric_name": metric_name,
            "value": round(value, 2),
            "host": random.choice(hosts),
        }

        docs.append({"_index": "system-metrics", "_source": doc})

    return docs


def main():
    print("Generating 20,000 metric data points...")
    metrics = generate_metrics(20000)

    print("Connecting to Elasticsearch...")
    es = get_es_client()

    print("Bulk indexing metrics...")
    helpers.bulk(es, metrics, chunk_size=500)

    print("Refreshing index...")
    es.indices.refresh(index="system-metrics")

    count = es.count(index="system-metrics")
    print(f"✅ Successfully indexed {count['count']} metrics!")

    # Show sample metric distribution
    result = es.search(
        index="system-metrics",
        body={
            "size": 0,
            "aggs": {"by_metric": {"terms": {"field": "metric_name", "size": 10}}},
        },
    )

    print("\n📊 Metric Distribution:")
    for bucket in result["aggregations"]["by_metric"]["buckets"]:
        print(f"   {bucket['key']}: {bucket['doc_count']} data points")


if __name__ == "__main__":
    main()
