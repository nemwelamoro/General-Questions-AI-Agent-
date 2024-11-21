from flask import Flask, request, jsonify
from query_agent import QueryAgent

app = Flask(__name__)
query_agent = QueryAgent()


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "Question not provided"}), 400

    answer = query_agent.answer_question(question)
    return jsonify({"question": question, "answer": answer})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
