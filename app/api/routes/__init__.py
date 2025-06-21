from flask import Blueprint
from .analyze import analyze_blueprint
from .health import health_blueprint

api_blueprint = Blueprint('api', __name__)

# 각각의 blueprint를 등록
api_blueprint.register_blueprint(analyze_blueprint)
api_blueprint.register_blueprint(health_blueprint) 