from flask import Flask, request
import os
import requests
import ecdsa
import base58
import hashlib
import json

app = Flask(__name__)

# ================== BASIC ==================

@app.route('/')
def home():
    return {"status": "server running"}

@app.route("/check-key")
def check_key():
    key = os.getenv("ADMIN_PRIVATE_KEY")
    return {"status": "key loaded" if key else "no key"}

# ================== WALLET ==================

@app.route("/create-wallet", methods=["POST"])
def create_wallet():
    data = request.json
    user_id = data.get("user_id")

    private_key = os.urandom(32)

    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()

    sha256 = hashlib.sha256(public_key).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()

    address = b'\x41' + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    address_base58 = base58.b58encode(address + checksum)

    wallet_data = {
        "address": address_base58.decode(),
        "private_key": private_key.hex()
    }

    try:
        with open("wallets.json", "r") as f:
            all_wallets = json.load(f)
    except:
        all_wallets = {}

    all_wallets[user_id] = wallet_data

    with open("wallets.json", "w") as f:
        json.dump(all_wallets, f)

    return {
        "user_id": user_id,
        "address": wallet_data["address"],
        "private_key": "hidden"
    }

# ================== UTILS ==================

def base58_to_hex(address):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = 0
    for char in address:
        num = num * 58 + alphabet.index(char)

    hex_str = hex(num)[2:]
    if len(hex_str) % 2:
        hex_str = '0' + hex_str

    return hex_str

def encode_parameter(to_address, amount):
    to_hex = base58_to_hex(to_address)[2:]
    to_padded = to_hex.rjust(64, '0')
    amount_hex = hex(amount)[2:].rjust(64, '0')
    return to_padded + amount_hex

# ================== BUILD USDT ==================

@app.route("/build-usdt")
def build_usdt():
    owner = "TGE4C7ai7i1MbETfKrRC4N7SAJSTppJAcx"
    to = "TNXsX7LJA521ifTvLxUPTycsiXrChut7zg"

    amount = 1_000_000

    parameter = encode_parameter(to, amount)

    payload = {
        "owner_address": base58_to_hex(owner),
        "contract_address": "41a614f803b6fd780986a42c78ec9c7f77e6ded13c",
        "function_selector": "transfer(address,uint256)",
        "parameter": parameter,
        "fee_limit": 100000000,
        "call_value": 0,
        "visible": False
    }

    r = requests.post(
        "https://api.trongrid.io/wallet/triggersmartcontract",
        json=payload
    )

    return r.json()

# ================== SIGN (USER BASED) ==================

@app.route("/sign-and-send", methods=["POST"])
def sign_and_send():
    try:
        data = request.json
        tx = data.get("tx")
        user_id = data.get("user_id")

        with open("wallets.json", "r") as f:
            wallets = json.load(f)

        private_key_hex = wallets[user_id]["private_key"]
        private_key = bytes.fromhex(private_key_hex)

        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        txid = bytes.fromhex(tx["txID"])
        signature = sk.sign_digest(txid)

        tx["signature"] = [signature.hex()]

        r = requests.post(
            "https://api.trongrid.io/wallet/broadcasttransaction",
            json=tx
        )

        return r.json()

    except Exception as e:
        return {"error": str(e)}

# ================== SEND DIRECT ==================

@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json
        user_id = data.get("user_id")
        to = data.get("to")
        amount = float(data.get("amount"))

        with open("wallets.json", "r") as f:
            wallets = json.load(f)

        private_key_hex = wallets[user_id]["private_key"]
        private_key = bytes.fromhex(private_key_hex)

        owner = wallets[user_id]["address"]
        parameter = encode_parameter(to, int(amount * 1_000_000))

        payload = {
            "owner_address": base58_to_hex(owner),
            "contract_address": "41a614f803b6fd780986a42c78ec9c7f77e6ded13c",
            "function_selector": "transfer(address,uint256)",
            "parameter": parameter,
            "fee_limit": 100000000,
            "call_value": 0,
            "visible": False
        }

        build = requests.post(
            "https://api.trongrid.io/wallet/triggersmartcontract",
            json=payload
        ).json()

        tx = build["transaction"]

        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        txid = bytes.fromhex(tx["txID"])
        signature = sk.sign_digest(txid)

        tx["signature"] = [signature.hex()]

        result = requests.post(
            "https://api.trongrid.io/wallet/broadcasttransaction",
            json=tx
        ).json()

        return result

    except Exception as e:
        return {"error": str(e)}

# ================== GET BALANCE ==================

@app.route("/get-balance")
def get_balance():
    try:
        user_id = request.args.get("user_id")

        with open("wallets.json", "r") as f:
            wallets = json.load(f)

        address = wallets[user_id]["address"]

        url = f"https://api.trongrid.io/v1/accounts/{address}"
        r = requests.get(url).json()

        balance = 0

        if "data" in r and len(r["data"]) > 0:
            tokens = r["data"][0].get("trc20", [])
            for t in tokens:
                if "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj" in t:
                    balance = int(t["TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"]) / 1_000_000

        return {
            "user_id": user_id,
            "address": address,
            "usdt_balance": balance
        }

    except Exception as e:
        return {"error": str(e)}

# ================== SEND NOW ==================

@app.route("/send-now")
def send_now():
    try:
        build = requests.get("https://tron-project.onrender.com/build-usdt").json()

        tx = build["result"]["transaction"]

        private_key_hex = os.getenv("ADMIN_PRIVATE_KEY")
        private_key = bytes.fromhex(private_key_hex)

        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        txid = bytes.fromhex(tx["txID"])
        signature = sk.sign_digest(txid)

        tx["signature"] = [signature.hex()]

        r = requests.post(
            "https://api.trongrid.io/wallet/broadcasttransaction",
            json=tx
        )

        return r.json()

    except Exception as e:
        return {"error": str(e)}

# ================== RUN ==================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
