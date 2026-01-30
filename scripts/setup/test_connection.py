#!/usr/bin/env python3
"""Test connection to Elasticsearch"""

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import sys

def test_connection():
    """Test Elasticsearch connection"""
    load_dotenv()
    
    endpoint = os.getenv('ELASTIC_ENDPOINT')
    username = os.getenv('ELASTIC_USERNAME')
    password = os.getenv('ELASTIC_PASSWORD')
    
    if not all([endpoint, username, password]):
        print("❌ Missing credentials in .env file")
        print("Please check ELASTIC_ENDPOINT, ELASTIC_USERNAME, ELASTIC_PASSWORD")
        sys.exit(1)
    
    try:
        es = Elasticsearch(
            endpoint,
            basic_auth=(username, password),
            verify_certs=True
        )
        
        info = es.info()
        print("✅ Successfully connected to Elasticsearch!")
        print(f"   Cluster: {info['cluster_name']}")
        print(f"   Version: {info['version']['number']}")
        print(f"   Nodes: {info['cluster_name']}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)