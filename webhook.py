from allennlp.predictors.predictor import Predictor
from flask import Flask, request, jsonify
from nltk.corpus import wordnet as wn
import nltk

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
        response_dict = getattr(chatbot_func, req['handler']['name'])(userSay, session_id, time, predictor)
    except TypeError:
        response_dict = getattr(chatbot_func, req['handler']['name'])(req)

    return jsonify(response_dict)


if __name__ == "__main__":
    wn._morphy("test", pos='v')
    nltk.download('stopwords')
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
    app.run(debug=True, port=8888)
