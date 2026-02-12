from flask import Flask, request, jsonify, render_template_string
from agents.gemini_orchestrator import IncidentCommander

app = Flask(__name__)
commander = IncidentCommander()

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Incident & Data Commander</title>
<style>
body {
    font-family: Arial;
    background: #0f172a;
    color: white;
    padding: 40px;
}
.container {
    max-width: 900px;
    margin: auto;
}
textarea {
    width: 100%;
    height: 120px;
    padding: 15px;
    font-size: 16px;
    border-radius: 8px;
}
button {
    padding: 15px;
    margin-top: 15px;
    width: 100%;
    font-size: 18px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
}
.response {
    margin-top: 30px;
    background: #1e293b;
    padding: 20px;
    border-radius: 8px;
    white-space: pre-wrap;
}
</style>
</head>
<body>
<div class="container">
<h1>🚨 Incident & Data Commander</h1>
<textarea id="query" placeholder="Check for incidents or pipeline health..."></textarea>
<button onclick="send()">Analyze</button>
<div id="response" class="response"></div>
</div>

<script>
async function send() {
    const query = document.getElementById("query").value;
    const res = await fetch("/query", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query})
    });
    const data = await res.json();
    document.getElementById("response").innerText = data.response;
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
