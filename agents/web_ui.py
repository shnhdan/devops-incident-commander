from flask import Flask, request, jsonify, render_template_string
from gemini_orchestrator import IncidentCommander

app = Flask(__name__)
commander = IncidentCommander()

HTML = """ 
<!DOCTYPE html>
<html>
<head>
<title>Incident & Data Commander</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a;
    color: #e2e8f0;
}

.header {
    background: linear-gradient(90deg, #1e293b, #0f172a);
    padding: 25px;
    text-align: center;
    border-bottom: 1px solid #1f2937;
}

.header h1 {
    margin: 0;
    font-size: 26px;
}

.status {
    margin-top: 8px;
    font-size: 13px;
    color: #94a3b8;
}

.container {
    max-width: 1000px;
    margin: 40px auto;
    padding: 20px;
}

.card {
    background: #1e293b;
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

textarea {
    width: 100%;
    height: 100px;
    background: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    font-size: 15px;
    resize: none;
}

button {
    margin-top: 15px;
    padding: 12px 20px;
    font-size: 15px;
    background: #2563eb;
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
}

button:hover {
    background: #1d4ed8;
}

.quick-buttons button {
    background: #334155;
    margin: 5px;
}

.quick-buttons button:hover {
    background: #475569;
}

.response {
    margin-top: 20px;
    padding: 20px;
    background: #0f172a;
    border-left: 5px solid #2563eb;
    border-radius: 8px;
    white-space: pre-wrap;
    font-size: 14px;
}

.loading {
    display: none;
    margin-top: 15px;
    color: #60a5fa;
}

.spinner {
    border: 3px solid #1e293b;
    border-top: 3px solid #2563eb;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 10px;
}

@keyframes spin {
    100% { transform: rotate(360deg); }
}
</style>
</head>

<body>

<div class="header">
    <h1>🚨 Incident & Data Commander</h1>
    <div class="status">
        Local LLM: phi3:mini | Elasticsearch Connected | Slack Alerts Enabled
    </div>
</div>

<div class="container">

    <div class="card">
     <h3>Run Analysis</h3>
        <textarea id="query" placeholder="Ask about incidents, metrics, or pipeline health..."></textarea>
        <button onclick="sendQuery()">Analyze</button>

        <div class="quick-buttons">
            <button onclick="setQuery('Check for error spikes')">Error Spikes</button>
            <button onclick="setQuery('Show metric anomalies')">Metric Anomalies</button>
            <button onclick="setQuery('Check data pipeline health')">Pipeline Health</button>
            <button onclick="setQuery('Analyze ingestion trend')">Ingestion Trend</button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
               Processing...
               </div>

        <div id="response" class="response"></div>
     </div>

</div>

<script>
function setQuery(text) {
    document.getElementById("query").value = text;
}

async function sendQuery() {
    const query = document.getElementById("query").value;
    if (!query) return;

    document.getElementById("loading").style.display = "block";
    document.getElementById("response").innerText = "";

    const res = await fetch("/query", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query})
    });

    const data = await res.json();

    document.getElementById("loading").style.display = "none";

            let responseDiv = document.getElementById("response");

            try {
            let parsed = JSON.parse(data.response);

            if (Array.isArray(parsed) && parsed[0].percent_change !== undefined) {
            let html = "";

            parsed.forEach(item => {
            let color = "#2563eb";

            if (item.percent_change < -30) {
            color = "#dc2626";
            } else if (item.percent_change > 30) {
            color = "#16a34a";
            }

            html += `
            <div style="margin-bottom:15px; padding:15px; background:#0f172a; border-left:5px solid ${color}; border-radius:6px;">
            <strong>${item.index}</strong><br>
            Last 24h: ${item.last_24h}<br>
            Previous 24h: ${item.prev_24h}<br>
            Change: ${item.percent_change}%
            </div>`;
            });

            responseDiv.innerHTML = html;
            return;
            }

            } catch (e) {
            // Not JSON → continue normal rendering
            }

            responseDiv.innerText = data.response;

            // Severity styling for normal responses
            if (data.response.includes("CRITICAL")) {
            responseDiv.style.borderLeft = "5px solid #dc2626";
            } else if (data.response.includes("WARNING")) {
            responseDiv.style.borderLeft = "5px solid #f59e0b";
            } else {
            responseDiv.style.borderLeft = "5px solid #2563eb";
            }

            }
</script>

</body>
</html>

""" 

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_query = data.get("query", "")
    result = commander.decide_and_execute(user_query)
    return jsonify({"response": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
