from flask import Blueprint, request, jsonify
from app.models.schemas import DiaryEntryRequest
from app.services import ai_generator

bp = Blueprint('diary', __name__, url_prefix='/api')

@bp.route('/generate', methods=['POST'])
def generate_comic():
    try:
        data = request.get_json()
        diary_entry = DiaryEntryRequest(**data)
        
        # Start background job (threading)
        job_id = ai_generator.start_generation_job(diary_entry)
        
        return jsonify({"jobId": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
