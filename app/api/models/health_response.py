"""
HealthResponse data model
"""
from typing import Dict, Any


class HealthResponse:
    """Health response data model"""
    
    def __init__(self, status: str = "healthy", system_info: Dict[str, Any] = None, 
                 services: Dict[str, bool] = None):
        self.status = status
        self.system_info = system_info if system_info is not None else {}
        self.services = services if services is not None else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'status': self.status,
            'system_info': self.system_info,
            'services': self.services
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthResponse':
        """Create from dictionary"""
        return cls(
            status=data.get('status', 'healthy'),
            system_info=data.get('system_info', {}),
            services=data.get('services', {})
        )