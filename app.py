from flask import Flask, jsonify
 
app = Flask(__name__)
 
@app.route("/health", methods=["GET"])
def health():
<<<<<<< HEAD
    return jsonify({"status": "testingrishibhaiprodlatest"})
=======
    return jsonify({"status": "testingrishibhaidev is healthy again"})
>>>>>>> UAT
 
@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello from Azure Web App"})
 
if __name__ == "__main__":
    app.run()