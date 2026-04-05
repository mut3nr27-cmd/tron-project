from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Server running"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    return jsonify({"message": f"User {username} registered"})

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    msg = data.get("message")
    return jsonify({"message": f"Sent: {msg}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
