from flask import Blueprint, jsonify

bp = Blueprint('artifacts', __name__, url_prefix='/api/artifacts')

# Implementation pending actual logic, keeping it minimal as per original file structure likely
# Original file content was small, just placeholder usually.

@bp.route('/', methods=['GET'])
def list_artifacts():
    return jsonify([])
