import os
import ecdsa
import base58
import hashlib

# توليد محفظة
@app.route("/create-wallet")
def create_wallet():
    # توليد private key
    private_key = os.urandom(32)

    # public key
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()

    # hash
    sha256 = hashlib.sha256(public_key).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()

    address = b'\x41' + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    address_base58 = base58.b58encode(address + checksum)

    return {
        "address": address_base58.decode(),
        "private_key": private_key.hex()
    }
