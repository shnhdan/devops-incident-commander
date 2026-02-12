#!/usr/bin/env python3
"""Generate realistic application logs"""

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


def generate_logs(count=10000):
    """Generate realistic application logs with errors"""

    services = [
        "api-gateway",
        "payment-service",
        "user-service",
        "auth-service",
        "order-service",
    ]
    hosts = ["prod-01", "prod-02", "prod-03", "prod-04", "prod-05"]

    error_patterns = [
        (
            "DatabaseConnectionError",
            "CRITICAL",
            "Unable to connect to database - connection pool exhausted",
        ),
        (
            "HighLatency",
            "ERROR",
            "Request timeout after 30s - downstream service unreachable",
        ),
        (
            "OutOfMemory",
            "CRITICAL",
            "Java heap space exhausted - application requires restart",
        ),
        ("RateLimitExceeded", "WARN", "API rate limit exceeded - throttling requests"),
        ("AuthenticationFailure", "ERROR", "Invalid JWT token - authentication failed"),
    ]

    normal_messages = [
        "Request processed successfully",
        "Cache hit for user session",
        "User authentication successful",
        "Payment transaction completed",
        "Order created and queued for processing",
        "Database query executed in 45ms",
        "API response returned with 200 OK",
    ]

    docs = []
    now = datetime.utcnow()

    for i in range(count):
        # 5% error rate
        is_error = random.random() < 0.05

        if is_error:
            error_code, severity, message = random.choice(error_patterns)
        else:
            severity = "INFO"
            error_code = None
            message = random.choice(normal_messages)

        # Distribute timestamps over last 7 days
        timestamp = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        doc = {
            "@timestamp": timestamp.isoformat(),
            "service_name": random.choice(services),
            "severity": severity,
            "message": message,
            "host": random.choice(hosts),
            "trace_id": f"trace-{random.randint(100000, 999999)}",
        }

        if error_code:
            doc["error_code"] = error_code

        docs.append({"_index": "app-logs", "_source": doc})

    return docs


def main():
    print("Generating 10,000 application logs...")
    logs = generate_logs(10000)

    print("Connecting to Elasticsearch...")
    es = get_es_client()

    print("Bulk indexing logs...")
    helpers.bulk(es, logs, chunk_size=500)

    print("Refreshing index...")
    es.indices.refresh(index="app-logs")

    count = es.count(index="app-logs")
    print(f"✅ Successfully indexed {count['count']} logs!")

    # Show sample error distribution
    result = es.search(
        index="app-logs",
        body={
            "size": 0,
            "query": {"term": {"severity": "CRITICAL"}},
            "aggs": {"by_error": {"terms": {"field": "error_code", "size": 10}}},
        },
    )

    print("\n📊 Error Distribution:")
    for bucket in result["aggregations"]["by_error"]["buckets"]:
        print(f"   {bucket['key']}: {bucket['doc_count']} errors")


if __name__ == "__main__":
    main()
