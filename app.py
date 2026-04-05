from flask import Flask, request
import os
import requests
import ecdsa
import base58
import hashlib

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

@app.route("/create-wallet")
def create_wallet():
    private_key = os.urandom(32)

    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()

    sha256 = hashlib.sha256(public_key).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()

    address = b'\x41' + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    address_base58 = base58.b58encode(address + checksum)

    return {
        "address": address_base58.decode(),
        "private_key": private_key.hex()
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
    # إزالة 41 prefix
    to_hex = base58_to_hex(to_address)[2:]
    to_padded = to_hex.rjust(64, '0')
    amount_hex = hex(amount)[2:].rjust(64, '0')
    return to_padded + amount_hex

# ================== BUILD USDT ==================

@app.route("/build-usdt")
def build_usdt():
    owner = "TGE4C7ai7i1MbETfKrRC4N7SAJSTppJAcx"
    to = "TNXsX7LJA521ifTvLxUPTycsiXrChut7zg"

    amount = 1_000_000  # 1 USDT

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
@app.route("/sign-and-send", methods=["POST"])
def sign_and_send():
    try:
        data = request.json
        tx = data.get("tx")

        private_key_hex = os.getenv("ADMIN_PRIVATE_KEY")
        private_key = bytes.fromhex(private_key_hex)

        import ecdsa
        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        txid = bytes.fromhex(tx["txID"])
        signature = sk.sign_digest(txid)

        tx["signature"] = [signature.hex()]

        import requests
        r = requests.post(
            "https://api.trongrid.io/wallet/broadcasttransaction",
            json=tx
        )

        return r.json()

    except Exception as e:
        return {"error": str(e)}
        @app.route("/send-now")
def send_now():
    try:
        # نبني الترانزكشن
        build = requests.get("https://tron-project.onrender.com/build-usdt").json()

        tx = build["result"]["transaction"]

        private_key_hex = os.getenv("ADMIN_PRIVATE_KEY")
        private_key = bytes.fromhex(private_key_hex)

        import ecdsa
        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

        txid = bytes.fromhex(tx["txID"])
        signature = sk.sign_digest(txid)

        tx["signature"] = [signature.hex()]

        # إرسال
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
