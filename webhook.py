from flask import Flask, request, jsonify
import chatbot_func

app = Flask(__name__)


@app.route('/', methods=['POST'])
def webhook():
    req = request.get_json()
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    print(req)

    try:
        response_dict = getattr(chatbot_func, req['handler']['name'])(userSay, session_id, time)
    except TypeError:
        response_dict = getattr(chatbot_func, req['handler']['name'])(req)

    return jsonify(response_dict)


if __name__ == "__main__":
    app.run(debug=True, port=8888)
