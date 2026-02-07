from flask import Flask, jsonify
from flask_cors import CORS
from app.routers import diary, jobs, artifacts

app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:3000"]}})

# Register Blueprints
app.register_blueprint(diary.bp)
app.register_blueprint(jobs.bp)
app.register_blueprint(artifacts.bp)

@app.route("/")
def read_root():
    return jsonify({"message": "Welcome to Cartoon Diary API"})

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
