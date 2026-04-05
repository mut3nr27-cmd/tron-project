from flask import Flask
import os
from tronpy import Tron
from tronpy.keys import PrivateKey

app = Flask(__name__)
client = Tron()

# الصفحة الرئيسية
@app.route('/')
def home():
    return {"status": "server running"}

# فحص المفتاح
@app.route("/check-key")
def check_key():
    key = os.getenv("ADMIN_PRIVATE_KEY")

    if key:
        return {"status": "key loaded"}
    else:
        return {"status": "no key"}

# توليد محفظة
@app.route("/create-wallet")
def create_wallet():
    wallet = client.generate_address()
    return {
        "address": wallet["base58check_address"],
        "private_key": wallet["private_key"]
    }

# تشغيل السيرفر
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
