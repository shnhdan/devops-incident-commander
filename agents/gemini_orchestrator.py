#!/usr/bin/env python3
"""
Incident Commander (Ollama + Slack + Data Engineering Mode)
"""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from ollama import Client

load_dotenv()

OLLAMA_MODEL = "tinyllama"
ollama_client = Client(host="http://127.0.0.1:11434")

es = Elasticsearch(
    os.getenv("ELASTIC_ENDPOINT"),
    basic_auth=(
        os.getenv("ELASTIC_USERNAME"),
        os.getenv("ELASTIC_PASSWORD"),
    ),
    verify_certs=True,
)

# --------------------------------------------------
# Slack
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

    payload = {"attachments": [{"color": color,
                                "blocks": [{"type": "header",
                                            "text": {"type": "plain_text",
                                                     "text": f"🚨 Incident Report - {severity}",
                                                     },
                                            },
                                           {"type": "section",
                                            "text": {"type": "mrkdwn",
                                                     "text": message,
                                                     },
                                            },
                                           {"type": "context",
                                            "elements": [{"type": "mrkdwn",
                                                          "text": f"Generated at {datetime.utcnow()} UTC",
                                                          }],
                                            },
                                           ],
                                }]}

    requests.post(webhook, json=payload)


# --------------------------------------------------
# Local LLM
# --------------------------------------------------
def generate_local(prompt):
    try:
        response = ollama_client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_predict": 200,
                "num_ctx": 512
            }
        )
        return response.get("response", "")
    except Exception as e:
        return f"LLM Error: {e}"


# --------------------------------------------------
# Incident Commander
# --------------------------------------------------
class IncidentCommander:

    # ----------- Incident Tools -------------

    def detect_error_spikes(self):
        query = """
        FROM app-logs
        | WHERE severity IN ("ERROR", "CRITICAL")
        | STATS error_count = COUNT(*) BY service_name
        | WHERE error_count > 5
        """
        return es.esql.query(query=query)["values"]

    def detect_metric_anomalies(self):
        query = """
        FROM system-metrics
        | STATS max_value = MAX(value) BY service_name, metric_name
        | WHERE max_value > 80
        """
        return es.esql.query(query=query)["values"]

    # ----------- Data Engineering Tool -------------

    def data_pipeline_health(self):
        """
        Data Engineer feature:
        Detect ingestion drop or abnormal pipeline activity.
        """
        indices = es.cat.indices(format="json")

        pipeline_data = []
        for index in indices:
            docs = int(index.get("docs.count", 0))
            store = index.get("store.size", "0b")

            pipeline_data.append({
                "index": index["index"],
                "doc_count": docs,
                "store_size": store
            })

        return pipeline_data

    # --------------------------------------------------

    def ingestion_trend_analysis(self):
        """
        Compare ingestion: last 24h vs previous 24h
        Detect pipeline drops or spikes
        """

    indices = ["app-logs", "system-metrics"]

    trend_data = []

    for index in indices:
        try:
            query = f"""
            FROM {index}
            | WHERE @timestamp > NOW() - 48h
            | EVAL period = CASE(
                @timestamp > NOW() - 24h, "last_24h",
                "prev_24h"
              )
            | STATS count = COUNT(*) BY period
            """

            result = es.esql.query(query=query)

            last_24h = 0
            prev_24h = 0

            for row in result["values"]:
                if row[0] == "last_24h":
                    last_24h = row[1]
                elif row[0] == "prev_24h":
                    prev_24h = row[1]

            change = 0
            if prev_24h > 0:
                change = ((last_24h - prev_24h) / prev_24h) * 100

            trend_data.append({
                "index": index,
                "last_24h": last_24h,
                "prev_24h": prev_24h,
                "percent_change": round(change, 2)
            })

        except Exception as e:
            trend_data.append({
                "index": index,
                "error": str(e)
            })

    return trend_data

    # Orchestration
    # --------------------------------------------------
    def decide_and_execute(self, user_query):

        decision_prompt = f"""
User query: {user_query}

Choose one tool:
- detect_errors
- detect_metrics
- data_pipeline_health
- ingestion_trend_analysis

Respond JSON:
{{ "tool": "tool_name" }}
"""

        decision_text = generate_local(decision_prompt)

        try:
            decision = json.loads(decision_text)
            tool = decision.get("tool", "detect_errors")
        except BaseException:
            tool = "detect_errors"

        tool_map = {
            "detect_errors": self.detect_error_spikes,
            "detect_metrics": self.detect_metric_anomalies,
            "data_pipeline_health": self.data_pipeline_health,
            "ingestion_trend_analysis": self.ingestion_trend_analysis,
        }

        results = tool_map.get(tool, self.detect_error_spikes)()

        summary_prompt = f"""
User Query: {user_query}

Results:
{json.dumps(results, indent=2)}

Summarize clearly.
If pipeline issues detected, mention DATA PIPELINE WARNING.
If errors high, mark CRITICAL.
"""

        summary = generate_local(summary_prompt)

        # Slack trigger
        send_slack_notification(summary)

        return summary
