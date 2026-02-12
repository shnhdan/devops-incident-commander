#!/usr/bin/env python3
"""
Local Ollama-powered Incident Commander
- Uses phi3:mini
- Slack Block Kit alerts
- No API keys required
"""

import json
import os
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from ollama import Client

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv()

OLLAMA_MODEL = "phi3:mini"

ollama_client = Client(host="http://localhost:11434")

es = Elasticsearch(
    os.getenv("ELASTIC_ENDPOINT"),
    basic_auth=(
        os.getenv("ELASTIC_USERNAME"),
        os.getenv("ELASTIC_PASSWORD"),
    ),
    verify_certs=True,
)

# --------------------------------------------------
# Slack Notification
# --------------------------------------------------
def send_slack_notification(message):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return

    severity = "INFO"
    color = "#2563eb"

    if "CRITICAL" in message.upper():
        severity = "CRITICAL"
        color = "#dc2626"
    elif "WARNING" in message.upper():
        severity = "WARNING"
        color = "#f59e0b"

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 Incident Report - {severity}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message,
                        },
                    },
                ],
            }
        ]
    }

    try:
        requests.post(webhook, json=payload)
    except Exception as e:
        print(f"Slack error: {e}")

# --------------------------------------------------
# Local LLM
# --------------------------------------------------
def generate_local(prompt):
    try:
        response = ollama_client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
        )
        return response["response"]
    except Exception as e:
        print(f"Ollama error: {e}")
        return "Local model failed."

# --------------------------------------------------
# Incident Commander
# --------------------------------------------------
class IncidentCommander:

    def detect_error_spikes(self):
        query = """
        FROM app-logs
        | WHERE severity IN ("ERROR", "CRITICAL")
        | STATS error_count = COUNT(*) BY service_name
        | WHERE error_count > 5
        """
        try:
            result = es.esql.query(query=query)
            return result["values"]
        except Exception as e:
            return {"error": str(e)}

    def detect_metric_anomalies(self):
        query = """
        FROM system-metrics
        | STATS max_value = MAX(value) BY service_name, metric_name
        | WHERE max_value > 80
        """
        try:
            result = es.esql.query(query=query)
            return result["values"]
        except Exception as e:
            return {"error": str(e)}

    def analyze_with_enrichment(self):
        query = """
        FROM app-logs
        | WHERE severity == "CRITICAL"
        | STATS error_count = COUNT(*) BY service_name
        | WHERE error_count > 5
        """
        try:
            result = es.esql.query(query=query)
            return result["values"]
        except Exception as e:
            return {"error": str(e)}

    def search_runbooks(self, search_term="error"):
        try:
            result = es.search(
                index="runbooks",
                body={
                    "query": {
                        "multi_match": {
                            "query": search_term,
                            "fields": ["error_pattern^3", "title^2", "solution"],
                        }
                    },
                    "size": 3,
                },
            )
            return [hit["_source"] for hit in result["hits"]["hits"]]
        except Exception as e:
            return {"error": str(e)}

    def decide_and_execute(self, user_query):

        decision_prompt = f"""
User query: {user_query}

Choose one tool:
- detect_errors
- detect_metrics
- analyze_incident
- search_runbook

Respond JSON:
{{ "tool": "tool_name" }}
"""

        decision_text = generate_local(decision_prompt)

        try:
            decision = json.loads(decision_text)
            tool = decision.get("tool", "detect_errors")
        except:
            tool = "detect_errors"

        tool_map = {
            "detect_errors": self.detect_error_spikes,
            "detect_metrics": self.detect_metric_anomalies,
            "analyze_incident": self.analyze_with_enrichment,
            "search_runbook": self.search_runbooks,
        }

        results = tool_map.get(tool, self.detect_error_spikes)()

        format_prompt = f"""
User Query: {user_query}

Results:
{json.dumps(results, indent=2)}

Summarize clearly. Mention severity.
"""

        summary = generate_local(format_prompt)

        send_slack_notification(summary)

        return summary

# --------------------------------------------------
# CLI
# --------------------------------------------------
if __name__ == "__main__":
    commander = IncidentCommander()

    print("🚨 Incident Commander (Ollama Mode)")
    while True:
        query = input("\n💬 You: ")
        if query.lower() in ["quit", "exit"]:
            break

        response = commander.decide_and_execute(query)
        print("\n📊 Incident Report:\n")
        print(response)
