from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "vignesh123"


@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("MODE =", mode)
    print("TOKEN =", token)
    print("CHALLENGE =", challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    print("MESSAGE RECEIVED")
    print(data)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)