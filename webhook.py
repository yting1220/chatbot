from allennlp.predictors.predictor import Predictor
from flask import Flask, request, jsonify
from nltk.corpus import wordnet as wn
import nltk
import chatbot_func

app = Flask(__name__)


@app.route('/', methods=['POST'])
def webhook():
    req = request.get_json()
    print(req)
    try:
        if req['handler']['name'] == 'actions.handler.HEALTH_CHECK':
            response_dict = {"scene": {
                "next": {
                    'name': 'End conversation'
                }
            }}
        elif req['handler']['name'] == 'evaluate':
            response_dict = getattr(chatbot_func, req['handler']['name'])(req, predictor)
        elif req['handler']['name'] == 'expand':
            response_dict = getattr(chatbot_func, req['handler']['name'])(req)
        else:
            response_dict = getattr(chatbot_func, req['handler']['name'])(req)
    except TypeError:
        response_dict = getattr(chatbot_func, req['handler']['name'])()
    return jsonify(response_dict)


if __name__ == "__main__":
    wn._morphy("test", pos='v')
    nltk.download('stopwords')
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
    app.run(debug=True, port=8080)
