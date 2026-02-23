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
.container {
    max-width: 1000px;
    margin: 40px auto;
    padding: 20px;
}
.card {
    background: #1e293b;
    padding: 25px;
    border-radius: 12px;
}
textarea {
    width: 100%;
    height: 100px;
    background: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
}
button {
    margin-top: 15px;
    padding: 12px 20px;
    background: #2563eb;
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
}
.response {
    margin-top: 20px;
    padding: 20px;
    background: #0f172a;
    border-left: 5px solid #2563eb;
    border-radius: 8px;
    white-space: pre-wrap;
}
.loading {
    display: none;
    margin-top: 15px;
}
.spinner {
    border: 3px solid #1e293b;
    border-top: 3px solid #2563eb;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    100% { transform: rotate(360deg); }
}
</style>
</head>

<body>

<div class="header">
<h1>🚨 Incident & Data Commander</h1>
</div>

<div class="container">
<div class="card">

<textarea id="query" placeholder="Ask about incidents or metrics..."></textarea>
<button onclick="sendQuery()">Analyze</button>

<div class="loading" id="loading">
<div class="spinner"></div> Processing...
</div>

<div id="response" class="response"></div>

</div>
</div>

<script>

async function sendQuery(){
    const query=document.getElementById("query").value;
    if(!query) return;

    document.getElementById("loading").style.display="block";

    const res=await fetch("/query",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({query})
    });

    const data=await res.json();
    document.getElementById("loading").style.display="none";

    let box=document.getElementById("response");
    box.innerText=data.response;

    if(data.response.includes("CRITICAL"))
        box.style.borderLeft="5px solid #dc2626";
    else if(data.response.includes("WARNING"))
        box.style.borderLeft="5px solid #f59e0b";
    else
        box.style.borderLeft="5px solid #2563eb";
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
    user_query = request.json.get("query", "")
    result = commander.decide_and_execute(user_query)
    return jsonify({"response": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)