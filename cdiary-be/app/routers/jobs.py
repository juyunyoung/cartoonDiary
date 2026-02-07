from flask import Blueprint, jsonify
from app.services import ai_generator

bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

@bp.route('/<jobId>', methods=['GET'])
def get_job_status(jobId):
    status = ai_generator.get_job_status(jobId)
    if not status:
        return jsonify({"detail": "Job not found"}), 404
    return jsonify(status)
