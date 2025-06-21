"""
Swagger models for Flask-RESTX API documentation
"""
from flask_restx import fields


def create_swagger_models(api):
    """Create all Swagger models for API documentation"""
    
    # Text block model
    text_block_model = api.model('TextBlock', {
        'text': fields.String(required=True, description='Extracted text', example='Sample text'),
        'bbox': fields.List(fields.Integer, required=True, description='Bounding box [x, y, width, height]', example=[100, 100, 400, 50]),
        'page_idx': fields.Integer(required=True, description='Page index', example=0),
        'id': fields.String(required=True, description='Block ID', example='block_1'),
        'block_type': fields.String(required=True, description='Block type from Marker', example='Text')
    })
    
    # Reference model
    reference_model = api.model('Reference', {
        'text': fields.String(required=True, description='Reference text', example='Figure 1'),
        'bbox': fields.List(fields.Integer, required=True, description='Bounding box [x, y, width, height]', example=[100, 100, 400, 50]),
        'figure_id': fields.String(required=True, description='Figure ID', example='fig_1'),
        'not_matched': fields.Boolean(required=True, description='Whether reference was not matched', example=False)
    })
    
    # Page model
    page_model = api.model('Page', {
        'index': fields.Integer(required=True, description='Page index', example=0),
        'page_size': fields.List(fields.Integer, required=True, description='Page dimensions [width, height]', example=[612, 792]),
        'blocks': fields.List(fields.Nested(text_block_model), required=True, description='Text blocks on page'),
        'references': fields.List(fields.Nested(reference_model), required=True, description='References on page')
    })
    
    # Metadata model
    metadata_model = api.model('Metadata', {
        'filename': fields.String(required=True, description='Original filename', example='sample.pdf'),
        'total_pages': fields.Integer(required=True, description='Total number of pages', example=10),
        'file_size': fields.Integer(required=True, description='File size in bytes', example=1024000),
        'processing_time': fields.Float(required=True, description='Processing time in seconds', example=5.23),
        'processor': fields.String(required=True, description='Processing method used', example='marker'),
        'table_of_contents': fields.List(fields.Raw, description='Marker table of contents (if available)'),
        'page_stats': fields.List(fields.Raw, description='Marker page statistics (if available)')
    })
    
    # Analysis response model
    analysis_response_model = api.model('AnalysisResponse', {
        'metadata': fields.Nested(metadata_model, required=True, description='Document metadata'),
        'pages': fields.List(fields.Nested(page_model), required=True, description='Extracted pages data')
    })
    
    # Stream response model
    stream_response_model = api.model('StreamResponse', {
        'status': fields.String(required=True, description='Status of the operation', example='progress'),
        'message': fields.String(required=True, description='Status message', example='Processing PDF'),
        'timestamp': fields.Float(required=True, description='Unix timestamp', example=1640995200.123),
        'data': fields.Raw(description='Response data (for completed status)'),
        'progress': fields.Integer(description='Progress percentage (0-100)', example=50, min=0, max=100)
    })
    
    # Health response model
    health_response_model = api.model('HealthResponse', {
        'status': fields.String(required=True, description='Health status', example='healthy', enum=['healthy', 'unhealthy']),
        'system_info': fields.Raw(required=True, description='System information'),
        'services': fields.Raw(required=True, description='Services status')
    })
    
    # Error response model
    error_response_model = api.model('ErrorResponse', {
        'error': fields.String(required=True, description='Error type', example='Bad request'),
        'message': fields.String(required=True, description='Error message', example='No file provided')
    })
    
    return {
        'text_block': text_block_model,
        'reference': reference_model,
        'page': page_model,
        'metadata': metadata_model,
        'analysis_response': analysis_response_model,
        'stream_response': stream_response_model,
        'health_response': health_response_model,
        'error_response': error_response_model
    }