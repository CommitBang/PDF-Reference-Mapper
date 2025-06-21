from flask import Flask, jsonify
from flask_cors import CORS
import logging
from app.config.settings import config
from app.api.routes import api_blueprint
from app.api.models import ErrorResponse


def create_app():
    app = Flask(__name__)
    api_config = config.get_api_config()
    processing_config = config.get_processing_config()
    app.config['MAX_CONTENT_LENGTH'] = api_config.get('max_file_size', 52428800)  # 50MB
    app.config['UPLOAD_TIMEOUT'] = api_config.get('upload_timeout', 300)
    CORS(app)
    log_level = processing_config.get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.register_blueprint(api_blueprint)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        error_response = ErrorResponse(error='Bad request', message=str(error))
        return jsonify(error_response.to_dict()), 400

    @app.errorhandler(413)
    def request_entity_too_large(error):
        error_response = ErrorResponse(error='File too large', message='Maximum file size is 50MB')
        return jsonify(error_response.to_dict()), 413

    @app.errorhandler(415)
    def unsupported_media_type(error):
        error_response = ErrorResponse(error='Unsupported media type', message='Only PDF files are supported')
        return jsonify(error_response.to_dict()), 415

    @app.errorhandler(500)
    def internal_server_error(error):
        error_response = ErrorResponse(error='Internal server error', message='An unexpected error occurred')
        return jsonify(error_response.to_dict()), 500

    return app


if __name__ == '__main__':
    app = create_app()
    api_config = config.get_api_config()
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 5000)
    print(f"Starting PDF Mapper API server on {host}:{port}")
    print(f"Swagger documentation available at: http://{host}:{port}/docs/")
    app.run(host=host, port=port, debug=False)