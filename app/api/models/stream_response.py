"""
StreamResponse data model
"""
from typing import Optional, Dict, Any
import time


class StreamResponse:
    """Stream response data model"""
    
    def __init__(self, status: str = "", message: str = "", data: Optional[Dict[str, Any]] = None, 
                 progress: Optional[int] = None, timestamp: float = None):
        self.status = status
        self.message = message
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.data = data
        self.progress = progress
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp
        }
        if self.data is not None:
            result['data'] = self.data
        if self.progress is not None:
            result['progress'] = self.progress
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamResponse':
        """Create from dictionary"""
        return cls(
            status=data.get('status', ''),
            message=data.get('message', ''),
            data=data.get('data'),
            progress=data.get('progress'),
            timestamp=data.get('timestamp', time.time())
        )