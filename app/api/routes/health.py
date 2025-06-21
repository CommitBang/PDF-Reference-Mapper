from flask import Blueprint, jsonify
from app.utils.gpu_utils import gpu_manager
from app.api.models import HealthResponse, ErrorResponse

health_blueprint = Blueprint('health', __name__)

@health_blueprint.route('/health', methods=['GET'])
def health():
    try:
        system_info = gpu_manager.get_system_info()
        health_response = HealthResponse(
            status='healthy',
            system_info=system_info,
            services={
                'marker_ocr_service': True,
                'gpu_available': system_info.get('gpu', {}).get('available', False)
            }
        )
        return jsonify(health_response.to_dict())
    except Exception as e:
        error_response = ErrorResponse(error='unhealthy', message=str(e))
        return jsonify(error_response.to_dict()), 500 