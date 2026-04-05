from flask import Flask

app = Flask(name)

@app.route("/")
def home():
    return "Server is running 🚀"

if name == "main":
    app.run(host="0.0.0.0", port=3000)