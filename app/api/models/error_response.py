"""
ErrorResponse data model
"""
from typing import Dict, Any


class ErrorResponse:
    """Error response data model"""
    
    def __init__(self, error: str = "", message: str = ""):
        self.error = error
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'error': self.error,
            'message': self.message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorResponse':
        """Create from dictionary"""
        return cls(
            error=data.get('error', ''),
            message=data.get('message', '')
        )