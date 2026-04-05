from flask import Flask, request, jsonify

app = Flask(__name__)

# الصفحة الرئيسية
@app.route("/")
def home():
    return "PayChat API is running 🚀"

# تسجيل مستخدم
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    return jsonify({"message": f"User {username} registered"})

# إرسال رسالة
@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    msg = data.get("message")
    return jsonify({"message": f"Sent: {msg}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
