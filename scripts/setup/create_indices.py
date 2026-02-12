#!/usr/bin/env python3
"""Create Elasticsearch indices for Incident Commander"""

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import sys


def get_es_client():
    """Get configured Elasticsearch client"""
    load_dotenv()
    return Elasticsearch(
        os.getenv("ELASTIC_ENDPOINT"),
        basic_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),
        verify_certs=True,
    )


def create_indices():
    """Create all required indices"""
    es = get_es_client()

    indices = {
        "app-logs": {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "service_name": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "message": {"type": "text"},
                    "error_code": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "trace_id": {"type": "keyword"},
                }
            }
        },
        "system-metrics": {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "service_name": {"type": "keyword"},
                    "metric_name": {"type": "keyword"},
                    "value": {"type": "float"},
                    "host": {"type": "keyword"},
                }
            }
        },
        "runbooks": {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "error_pattern": {"type": "text"},
                    "service": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "solution": {"type": "text"},
                    "commands": {"type": "text"},
                    "last_updated": {"type": "date"},
                }
            }
        },
        "service-inventory": {
            "mappings": {
                "properties": {
                    "service_name": {"type": "keyword"},
                    "team": {"type": "keyword"},
                    "oncall_slack_channel": {"type": "keyword"},
                    "pagerduty_service_id": {"type": "keyword"},
                    "criticality": {"type": "keyword"},
                }
            }
        },
    }

    for index_name, config in indices.items():
        if es.indices.exists(index=index_name):
            print(f"⚠️  Index '{index_name}' exists, deleting...")
            es.indices.delete(index=index_name)

        es.indices.create(index=index_name, body=config)
        print(f"✅ Created index: {index_name}")

    print(f"\n🎉 Successfully created {len(indices)} indices!")


if __name__ == "__main__":
    try:
        create_indices()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
