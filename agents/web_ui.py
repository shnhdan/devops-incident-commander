#!/usr/bin/env python3
"""Modern Web UI for Incident Commander"""

from flask import Flask, request, jsonify, render_template_string
from gemini_orchestrator import IncidentCommander

app = Flask(__name__)
commander = IncidentCommander()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Incident Commander</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
:root {
    --bg1: #0f172a;
    --bg2: #1e293b;
    --accent: #7c3aed;
    --accent2: #6366f1;
    --success: #10b981;
    --danger: #ef4444;
    --glass: rgba(255,255,255,0.05);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Inter, system-ui, -apple-system, sans-serif;
    background: linear-gradient(-45deg, #0f172a, #1e293b, #111827, #0f172a);
    background-size: 400% 400%;
    animation: gradientMove 15s ease infinite;
    color: white;
    min-height: 100vh;
    padding: 40px 20px;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.container {
    max-width: 1000px;
    margin: auto;
    background: var(--glass);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 25px 80px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.08);
}

.header {
    text-align: center;
    margin-bottom: 40px;
}

.header h1 {
    font-size: 2.8rem;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header p {
    opacity: 0.7;
    margin-top: 10px;
    font-size: 1.1rem;
}

.input-section {
    display: flex;
    gap: 15px;
    margin-bottom: 25px;
}

.query-box {
    flex: 1;
    padding: 18px 20px;
    font-size: 1rem;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(0,0,0,0.3);
    color: white;
    transition: 0.3s ease;
}

.query-box:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(124,58,237,0.3);
}

button {
    padding: 18px 30px;
    border-radius: 12px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    transition: 0.3s ease;
}

.primary-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: white;
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(124,58,237,0.4);
}

.primary-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.examples {
    margin: 25px 0;
}

.examples-title {
    margin-bottom: 15px;
    opacity: 0.8;
}

.example-btn {
    background: rgba(255,255,255,0.08);
    color: white;
    margin: 5px;
    padding: 10px 16px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 0.9rem;
}

.example-btn:hover {
    background: rgba(124,58,237,0.3);
}

.loading {
    text-align: center;
    display: none;
    margin-top: 20px;
}

.spinner {
    border: 3px solid rgba(255,255,255,0.2);
    border-top: 3px solid var(--accent);
    border-radius: 50%;
    width: 35px;
    height: 35px;
    animation: spin 1s linear infinite;
    margin: auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.response {
    margin-top: 30px;
    background: rgba(0,0,0,0.4);
    border-radius: 14px;
    padding: 25px;
    white-space: pre-wrap;
    line-height: 1.6;
    display: none;
    border-left: 4px solid var(--accent);
    font-family: monospace;
    font-size: 0.95rem;
}

.status {
    font-size: 0.9rem;
    opacity: 0.6;
    margin-top: 10px;
}

footer {
    margin-top: 30px;
    text-align: center;
    font-size: 0.8rem;
    opacity: 0.5;
}
</style>
</head>

<body>

<div class="container">

<div class="header">
    <h1>🚨 Incident Commander</h1>
    <p>Gemini + Elasticsearch Incident Orchestration</p>
</div>

<div class="input-section">
    <input type="text" id="query" class="query-box"
           placeholder="Ask about incidents, metrics, or search runbooks..."
           autofocus>
    <button class="primary-btn" id="submitBtn" onclick="submitQuery()">
        Analyze
    </button>
</div>

<div class="examples">
    <div class="examples-title">💡 Quick Commands</div>
    <button class="example-btn" onclick="setQuery('Check for incidents in the last hour')">Check Incidents</button>
    <button class="example-btn" onclick="setQuery('Analyze critical incidents')">Analyze Critical</button>
    <button class="example-btn" onclick="setQuery('Find runbook for DatabaseConnectionError')">Search Runbook</button>
    <button class="example-btn" onclick="setQuery('Show metric anomalies')">Metric Anomalies</button>
</div>

<div class="loading" id="loading">
    <div class="spinner"></div>
    <div class="status">Analyzing with Gemini + Elasticsearch...</div>
</div>

<div id="response" class="response"></div>

<footer>
    Incident Commander • Secure Local Execution • No Vendor Lock-in
</footer>

</div>

<script>
function setQuery(text) {
    document.getElementById("query").value = text;
}

async function submitQuery() {
    const query = document.getElementById("query").value.trim();
    if (!query) return;

    const btn = document.getElementById("submitBtn");
    btn.disabled = true;

    document.getElementById("loading").style.display = "block";
    document.getElementById("response").style.display = "none";

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query: query})
        });

        const data = await response.json();

        document.getElementById("loading").style.display = "none";
        document.getElementById("response").style.display = "block";
        document.getElementById("response").textContent = data.response;
    } catch (error) {
        document.getElementById("loading").style.display = "none";
        document.getElementById("response").style.display = "block";
        document.getElementById("response").textContent = "Error: " + error.message;
    }

    btn.disabled = false;
}

document.getElementById("query").addEventListener("keypress", function(e) {
    if (e.key === "Enter") submitQuery();
});
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
    return jsonify({"response": result["response"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
