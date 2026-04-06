from flask import Flask, request
import os
import requests
import ecdsa
import ecdsa.util
import base58
import hashlib
import json

app = Flask(__name__)

# ================== STORAGE ==================

def load_wallets():
    if not os.path.exists("wallets.json"):
        with open("wallets.json", "w") as f:
            json.dump({}, f)

    with open("wallets.json", "r") as f:
        return json.load(f)

def save_wallets(data):
    with open("wallets.json", "w") as f:
        json.dump(data, f)

# ================== BASIC ==================

@app.route('/')
def home():
    return {"status": "server running"}

# ================== WALLET ==================

@app.route("/create-wallet", methods=["POST"])
def create_wallet():
    data = request.json

    if not data or "user_id" not in data:
        return {"error": "user_id required"}

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

    wallets = load_wallets()
    wallets[user_id] = wallet_data
    save_wallets(wallets)

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
        if char not in alphabet:
            raise ValueError("Invalid address")
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

# ================== SEND ==================

@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json

        # تحقق من البيانات
        if not data:
            return {"error": "no data"}

        user_id = data.get("user_id")
        to = data.get("to")
        amount = data.get("amount")

        if not user_id or not to or not amount:
            return {"error": "missing fields"}

        amount = float(amount)

        wallets = load_wallets()

        if user_id not in wallets:
            return {"error": "user not found"}

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

        # ✅ تحقق من وجود transaction
        if "result" not in build or "transaction" not in build["result"]:
            return {"error": build}

        tx = build["result"]["transaction"]

        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        raw_data = bytes.fromhex(tx["raw_data_hex"])
        hash_data = hashlib.sha256(raw_data).digest()

        signature = sk.sign_digest(
            hash_data,
            sigencode=ecdsa.util.sigencode_string
        ) + b'\x01'

        tx["signature"] = [signature.hex()]

        result = requests.post(
            "https://api.trongrid.io/wallet/broadcasttransaction",
            json=tx
        ).json()

        return result

    except Exception as e:
        return {"error": str(e)}

# ================== BALANCE ==================

@app.route("/get-balance")
def get_balance():
    try:
        user_id = request.args.get("user_id")

        wallets = load_wallets()

        if user_id not in wallets:
            return {"error": "user not found"}

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

# ================== RUN ==================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
