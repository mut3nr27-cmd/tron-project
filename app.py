from flask import Flask, request
import os
from tronpy import Tron
from tronpy.keys import PrivateKey

app = Flask(__name__)
client = Tron()

USDT_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

@app.route('/')
def home():
    return {"status": "server running"}

@app.route("/create-wallet")
def create_wallet():
    wallet = client.generate_address()
    return wallet

@app.route("/send-usdt", methods=["POST"])
def send_usdt():
    try:
        data = request.json

        to_address = data.get("to")
        amount = float(data.get("amount"))

        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        pk = PrivateKey(bytes.fromhex(private_key))

        owner_address = pk.public_key.to_base58check_address()

        contract = client.get_contract(USDT_CONTRACT)

        txn = (
            contract.functions.transfer(
                to_address,
                int(amount * 1_000_000)
            )
            .with_owner(owner_address)
            .fee_limit(10_000_000)
            .build()
            .sign(pk)
        )

        result = txn.broadcast().wait()

        return {"result": result}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
