#!/usr/bin/env python3
"""
Gemini-powered orchestrator for Incident Commander
Replaces Agent Builder's LLM with external Gemini API calls
"""

import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Elasticsearch client
es = Elasticsearch(
    os.getenv("ELASTIC_ENDPOINT"),
    basic_auth=(os.getenv("ELASTIC_USERNAME"), os.getenv("ELASTIC_PASSWORD")),
    verify_certs=True,
)


class IncidentCommander:
    """Gemini-powered incident commander"""

    def __init__(self):
        self.tools = {
            "detect_errors": self.detect_error_spikes,
            "detect_metrics": self.detect_metric_anomalies,
            "analyze_incident": self.analyze_with_enrichment,
            "search_runbook": self.search_runbooks,
        }

    # --------------------------------------------------
    # TOOL 1 — Detect Error Spikes
    # --------------------------------------------------
    def detect_error_spikes(self, time_window="1 hour", threshold=10):
        """Execute ES|QL query to detect error spikes"""

        time_map = {
            "1 hour": "1h",
            "30 minutes": "30m",
            "24 hours": "24h",
            "1h": "1h",
            "30m": "30m",
        }
        esql_time = time_map.get(time_window, "1h")

        query = f"""
        FROM app-logs
        | WHERE @timestamp > NOW() - {esql_time}
        | WHERE severity IN ("ERROR", "CRITICAL")
        | STATS error_count = COUNT(*) BY service_name, error_code
        | WHERE error_count > {threshold}
        | SORT error_count DESC
        | LIMIT 20
        """

        try:
            result = es.esql.query(query=query)
            return {
                "success": True,
                "data": result["values"],
                "columns": [col["name"] for col in result["columns"]],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------
    # TOOL 2 — Detect Metric Anomalies
    # --------------------------------------------------
    def detect_metric_anomalies(self, time_window="1 hour"):
        """Execute ES|QL query to detect metric anomalies"""

        time_map = {
            "1 hour": "1h",
            "30 minutes": "30m",
            "24 hours": "24h",
            "1h": "1h",
            "30m": "30m",
        }
        esql_time = time_map.get(time_window, "1h")

        query = f"""
        FROM system-metrics
        | WHERE @timestamp > NOW() - {esql_time}
        | STATS
            avg_value = AVG(value),
            max_value = MAX(value),
            count = COUNT(*)
          BY service_name, metric_name
        | WHERE
            (metric_name == "cpu_usage" AND max_value > 85) OR
            (metric_name == "memory_usage" AND max_value > 85) OR
            (metric_name == "request_latency" AND max_value > 2000) OR
            (metric_name == "error_rate" AND max_value > 5)
        | SORT max_value DESC
        """

        try:
            result = es.esql.query(query=query)
            return {
                "success": True,
                "data": result["values"],
                "columns": [col["name"] for col in result["columns"]],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------
    # TOOL 3 — Analyze with Enrichment
    # --------------------------------------------------
    def analyze_with_enrichment(self, time_window="1 hour"):
        """Analyze incidents and enrich with service inventory"""

        time_map = {
            "1 hour": "1h",
            "30 minutes": "30m",
            "24 hours": "24h",
            "1h": "1h",
            "30m": "30m",
        }
        esql_time = time_map.get(time_window, "1h")

        query = f"""
        FROM app-logs
        | WHERE @timestamp > NOW() - {esql_time}
        | WHERE severity == "CRITICAL"
        | STATS
            error_count = COUNT(*),
            first_seen = MIN(@timestamp),
            last_seen = MAX(@timestamp),
            affected_hosts = COUNT_DISTINCT(host)
          BY service_name, error_code
        | WHERE error_count > 5
        | SORT error_count DESC
        | LIMIT 10
        """

        try:
            result = es.esql.query(query=query)

            enriched_data = []

            for row in result["values"]:
                service_name = row[0]

                service_info = es.search(
                    index="service-inventory",
                    body={"query": {"term": {"service_name": service_name}}},
                )

                if service_info["hits"]["total"]["value"] > 0:
                    service = service_info["hits"]["hits"][0]["_source"]
                    enriched_row = row + [
                        service.get("team", "unknown"),
                        service.get("oncall_slack_channel", "unknown"),
                        service.get("criticality", "unknown"),
                    ]
                else:
                    enriched_row = row + ["unknown", "unknown", "unknown"]

                enriched_data.append(enriched_row)

            return {
                "success": True,
                "data": enriched_data,
                "columns": [col["name"] for col in result["columns"]]
                + ["team", "slack_channel", "criticality"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------
    # TOOL 4 — Search Runbooks
    # --------------------------------------------------
    def search_runbooks(self, search_term):
        """Search runbooks using Elasticsearch"""

        try:
            result = es.search(
                index="runbooks",
                body={
                    "query": {
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "error_pattern^3",
                                "title^2",
                                "solution",
                                "service",
                            ],
                            "type": "best_fields",
                        }
                    },
                    "size": 3,
                },
            )

            runbooks = []
            for hit in result["hits"]["hits"]:
                runbooks.append(
                    {
                        "title": hit["_source"].get("title"),
                        "error_pattern": hit["_source"].get("error_pattern"),
                        "solution": hit["_source"].get("solution"),
                        "commands": hit["_source"].get("commands"),
                        "service": hit["_source"].get("service"),
                        "score": hit["_score"],
                    }
                )

            return {"success": True, "data": runbooks}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------
    # GEMINI DECISION ENGINE
    # --------------------------------------------------
    def decide_and_execute(self, user_query):
        """Use Gemini to decide tools and execute"""

        decision_prompt = f"""
You are an incident response orchestrator.

Available tools:
1. detect_errors(time_window, threshold)
2. detect_metrics(time_window)
3. analyze_incident(time_window)
4. search_runbook(search_term)

User query: "{user_query}"

Respond with JSON only:
{{
  "tools_to_use": ["tool_name"],
  "parameters": {{"tool_name": {{"param": "value"}}}},
  "reasoning": "why"
}}
"""

        try:
            response = model.generate_content(decision_prompt)
            decision = json.loads(response.text.strip())
            print(f"\n🤖 Gemini: {decision.get('reasoning', '')}")
        except Exception as e:
            print(f"⚠️ Decision error: {e}")
            decision = {
                "tools_to_use": ["detect_errors"],
                "parameters": {
                    "detect_errors": {
                        "time_window": "1 hour",
                        "threshold": 10,
                    }
                },
            }

        results = {}

        for tool_name in decision.get("tools_to_use", []):
            if tool_name in self.tools:
                params = decision.get("parameters", {}).get(tool_name, {})
                print(f"🔧 Executing: {tool_name}")
                results[tool_name] = self.tools[tool_name](**params)

        format_prompt = f"""
User Query: "{user_query}"
Tool Results: {json.dumps(results, indent=2)}

Summarize findings clearly and concisely.
"""

        try:
            response = model.generate_content(format_prompt)
            final_response = response.text
        except Exception as e:
            final_response = (
                f"Formatting error: {e}\n\nRaw Results:\n"
                + json.dumps(results, indent=2)
            )

        return {
            "decision": decision,
            "tool_results": results,
            "response": final_response,
        }


# --------------------------------------------------
# CLI
# --------------------------------------------------
def main():
    print("=" * 60)
    print("🚨 INCIDENT COMMANDER - Gemini Orchestrator")
    print("=" * 60)

    commander = IncidentCommander()

    while True:
        try:
            query = input("\n💬 You: ").strip()

            if query.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            print("\n🔍 Processing...")
            result = commander.decide_and_execute(query)

            print("\n" + "=" * 60)
            print("📊 INCIDENT REPORT")
            print("=" * 60)
            print(result["response"])
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
