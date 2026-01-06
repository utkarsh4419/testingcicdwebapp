from flask import Flask, jsonify
 
app = Flask(__name__)
 
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "testingrishibhaiprodlatest"})
 
@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello from Azure Web App"})
 
if __name__ == "__main__":
    app.run()