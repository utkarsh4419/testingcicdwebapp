from flask import Flask, jsonify
import os
 
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Dev branch is healthy again"})
 
@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello from Azure Web App"})

@app.route("/api/env", methods=["GET"])
def env():
    snow_get_url = os.getenv("snow_get")
    env= os.getenv("env")

    return jsonify({"message": "Hello this is utkarsh", "snow get": snow_get_url,"env": env})

if __name__ == "__main__":
    app.run()