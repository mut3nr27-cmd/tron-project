from flask import Flask, request, jsonify
from tronpy.keys import PrivateKey

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")

    private_key = PrivateKey.random()
    address = private_key.public_key.to_base58check_address()

    return jsonify({
        "user": username,
        "address": address,
        "private_key": private_key.hex()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
