#!/usr/bin/env python3
"""Create runbook knowledge base"""

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

RUNBOOKS = [
    {
        "title": "Database Connection Failure Recovery",
        "error_pattern": "DatabaseConnectionError Unable to connect connection pool exhausted",
        "service": "payment-service",
        "severity": "CRITICAL",
        "solution": """
Step 1: Check database pod health
   kubectl get pods -n database
   kubectl describe pod postgres-0

Step 2: Verify connection pool settings
   Check application.yaml for:
   - max_pool_size (should be 20-50)
   - connection_timeout (should be 30s)

Step 3: Restart affected service
   kubectl rollout restart deployment/payment-service
   kubectl rollout status deployment/payment-service

Step 4: If issue persists, scale database
   kubectl scale statefulset/postgres --replicas=3
   
Step 5: Monitor recovery
   kubectl logs -f deployment/payment-service | grep "Connected to database"
        """,
        "commands": "kubectl get pods -n database; kubectl logs -f deployment/payment-service",
        "last_updated": "2025-01-15T00:00:00Z"
    },
    {
        "title": "High Memory Usage - OOM Recovery",
        "error_pattern": "OutOfMemory Java heap space exhausted",
        "service": "api-gateway",
        "severity": "CRITICAL",
        "solution": """
Step 1: Identify high memory pods
   kubectl top pods --sort-by=memory
   
Step 2: Get heap dump for analysis
   kubectl exec api-gateway-xxx -- jmap -dump:live,format=b,file=/tmp/heap.hprof 1
   kubectl cp api-gateway-xxx:/tmp/heap.hprof ./heap.hprof
   
Step 3: Immediate mitigation - restart pod
   kubectl delete pod api-gateway-xxx
   
Step 4: Long-term fix - increase memory limit
   Edit deployment: memory: "2Gi" (from 1Gi)
   kubectl apply -f deployment.yaml
   
Step 5: Monitor after restart
   watch kubectl top pod api-gateway
   Check for memory leaks in application code
        """,
        "commands": "kubectl top pods; kubectl exec api-gateway-xxx -- jmap -dump",
        "last_updated": "2025-01-15T00:00:00Z"
    },
    {
        "title": "API Rate Limit Exceeded Response",
        "error_pattern": "RateLimitExceeded API rate limit throttling",
        "service": "user-service",
        "severity": "WARN",
        "solution": """
Step 1: Identify source of excessive requests
   grep 'RateLimitExceeded' /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn
   
Step 2: Determine if legitimate or abuse
   - Check if IP belongs to known customer
   - Review request patterns (same endpoint repeatedly?)
   
Step 3: If abuse, block offending IP
   Add to nginx blocklist:
   echo "deny 1.2.3.4;" >> /etc/nginx/blocked-ips.conf
   nginx -s reload
   
Step 4: If legitimate traffic spike
   Temporarily increase rate limit:
   Edit nginx.conf: limit_req_zone ... rate=100r/s (from 50r/s)
   nginx -s reload
   
Step 5: Notify customer success team
   If affecting paying customer, create support ticket
        """,
        "commands": "grep 'RateLimitExceeded' /var/log/nginx/access.log | head -20",
        "last_updated": "2025-01-15T00:00:00Z"
    },
    {
        "title": "Authentication Service Failure Recovery",
        "error_pattern": "AuthenticationFailure Invalid JWT token authentication failed",
        "service": "auth-service",
        "severity": "ERROR",
        "solution": """
Step 1: Check auth-service health endpoint
   curl http://auth-service.default.svc.cluster.local/health
   
Step 2: Verify JWT signing key hasn't rotated unexpectedly
   kubectl get secret jwt-signing-key -o yaml
   Compare with last known good value
   
Step 3: Check token expiration configuration
   Verify auth-service config: token_ttl: 3600 (1 hour)
   
Step 4: Restart auth-service if unhealthy
   kubectl rollout restart deployment/auth-service
   kubectl rollout status deployment/auth-service
   
Step 5: Clear cached credentials
   redis-cli -h redis.default.svc.cluster.local FLUSHDB
   
Step 6: Monitor authentication success rate
   Check Grafana dashboard: Authentication Success Rate
   Should return to >99% within 2 minutes
        """,
        "commands": "curl http://auth-service/health; kubectl rollout restart deployment/auth-service",
        "last_updated": "2025-01-15T00:00:00Z"
    },
    {
        "title": "High Request Latency Troubleshooting",
        "error_pattern": "HighLatency Request timeout downstream service unreachable",
        "service": "order-service",
        "severity": "ERROR",
        "solution": """
Step 1: Check downstream service health
   kubectl get pods -l app=database
   kubectl get pods -l app=cache
   curl http://payment-service/health
   
Step 2: Analyze slow query log
   tail -f /var/log/mysql/slow-query.log
   Look for queries >1s execution time
   
Step 3: Check cache hit rate
   redis-cli INFO stats | grep keyspace_hits
   redis-cli INFO stats | grep keyspace_misses
   Calculate hit rate: hits / (hits + misses)
   If <80%, investigate cache warming
   
Step 4: Profile application if CPU/memory bound
   Enable JMX profiling in deployment:
   JAVA_OPTS: "-Dcom.sun.management.jmxremote"
   
Step 5: Scale horizontally if resource constrained
   kubectl scale deployment/order-service --replicas=5
   Monitor: kubectl get hpa order-service
   
Step 6: Review recent deployments
   kubectl rollout history deployment/order-service
   Consider rollback if regression introduced
        """,
        "commands": "tail -f /var/log/mysql/slow-query.log; redis-cli INFO stats",
        "last_updated": "2025-01-15T00:00:00Z"
    }
]

def main():
    print("Creating runbook knowledge base...")
    es = get_es_client()
    
    for runbook in RUNBOOKS:
        es.index(index="runbooks", document=runbook)
        print(f"✅ Indexed: {runbook['title']}")
    
    es.indices.refresh(index="runbooks")
    
    count = es.count(index="runbooks")
    print(f"\n🎉 Successfully created {count['count']} runbooks!")

if __name__ == "__main__":
    main()