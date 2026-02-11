#!/usr/bin/env python3
"""Inject a test incident for e2e testing"""

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from datetime import datetime
import os

def get_es_client():
    load_dotenv()
    return Elasticsearch(
        os.getenv('ELASTIC_ENDPOINT'),
        basic_auth=(os.getenv('ELASTIC_USERNAME'), os.getenv('ELASTIC_PASSWORD')),
        verify_certs=True
    )

def inject_incident():
    """Inject realistic incident"""
    es = get_es_client()
    now = datetime.utcnow()
    
    print("💉 Injecting DatabaseConnectionError incident...")
    
    # Inject 50 critical errors
    docs = []
    for i in range(50):
        doc = {
            "@timestamp": now.isoformat(),
            "service_name": "payment-service",
            "severity": "CRITICAL",
            "message": "Unable to connect to database - connection pool exhausted",
            "error_code": "DatabaseConnectionError",
            "host": f"prod-0{i%5 + 1}",
            "trace_id": f"trace-{100000 + i}"
        }
        docs.append(doc)
        es.index(index="app-logs", document=doc)
    
    es.indices.refresh(index="app-logs")
    print(f"✅ Injected {len(docs)} critical errors")
    
    # Also inject high CPU metrics
    for i in range(20):
        metric = {
            "@timestamp": now.isoformat(),
            "service_name": "payment-service",
            "metric_name": "cpu_usage",
            "value": 95.0 + (i % 5),
            "host": f"prod-0{i%5 + 1}"
        }
        es.index(index="system-metrics", document=metric)
    
    es.indices.refresh(index="system-metrics")
    print(f"✅ Injected 20 metric anomalies")
    
    print("\n✅ Test incident injected!")
    print("Now run: python3 agents/gemini_orchestrator.py")
    print("And test: 'Check for incidents in the last hour'")

if __name__ == "__main__":
    inject_incident()