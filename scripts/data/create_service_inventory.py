#!/usr/bin/env python3
"""Create service inventory for LOOKUP JOINs"""

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

def get_es_client():
    load_dotenv()
    return Elasticsearch(
        os.getenv('ELASTIC_ENDPOINT'),
        basic_auth=(os.getenv('ELASTIC_USERNAME'), os.getenv('ELASTIC_PASSWORD')),
        verify_certs=True
    )

SERVICES = [
    {
        "service_name": "api-gateway",
        "team": "platform",
        "oncall_slack_channel": "#oncall-platform",
        "pagerduty_service_id": "PD-API-GATEWAY",
        "criticality": "high"
    },
    {
        "service_name": "payment-service",
        "team": "payments",
        "oncall_slack_channel": "#oncall-payments",
        "pagerduty_service_id": "PD-PAYMENTS",
        "criticality": "critical"
    },
    {
        "service_name": "user-service",
        "team": "identity",
        "oncall_slack_channel": "#oncall-identity",
        "pagerduty_service_id": "PD-USERS",
        "criticality": "high"
    },
    {
        "service_name": "auth-service",
        "team": "identity",
        "oncall_slack_channel": "#oncall-identity",
        "pagerduty_service_id": "PD-AUTH",
        "criticality": "critical"
    },
    {
        "service_name": "order-service",
        "team": "commerce",
        "oncall_slack_channel": "#oncall-commerce",
        "pagerduty_service_id": "PD-ORDERS",
        "criticality": "high"
    }
]

def main():
    print("Creating service inventory...")
    es = get_es_client()
    
    for service in SERVICES:
        es.index(index="service-inventory", document=service)
        print(f"✅ Indexed: {service['service_name']}")
    
    es.indices.refresh(index="service-inventory")
    
    count = es.count(index="service-inventory")
    print(f"\n🎉 Successfully created service inventory with {count['count']} services!")

if __name__ == "__main__":
    main()