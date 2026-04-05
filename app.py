import requests

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
    # تحويل العنوان لـ hex وإزالة prefix 41
    to_hex = base58_to_hex(to_address)[2:]

    # padding 64
    to_padded = to_hex.rjust(64, '0')
    amount_hex = hex(amount)[2:].rjust(64, '0')

    return to_padded + amount_hex


@app.route("/build-usdt")
def build_usdt():
    owner = "TGE4C7ai7i1MbETfKrRC4N7SAJSTppJAcx"
    to = "TNXsX7LJA521ifTvLxUPTycsiXrChut7zg"

    amount = 1_000_000  # 1 USDT

    parameter = encode_parameter(to, amount)

    payload = {
        "owner_address": owner,
        "contract_address": "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj",
        "function_selector": "transfer(address,uint256)",
        "parameter": parameter,
        "fee_limit": 100000000,
        "call_value": 0,
        "visible": True
    }

    r = requests.post(
        "https://api.trongrid.io/wallet/triggersmartcontract",
        json=payload
    )

    return r.json()
