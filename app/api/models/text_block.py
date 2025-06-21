"""
TextBlock data model
"""
from typing import List, Dict, Any


class TextBlock:
    """Text block data model"""
    
    def __init__(self, text: str = "", bbox: List[int] = None, page_idx: int = 0, 
                 block_id: str = "", block_type: str = ""):
        self.text = text
        self.bbox = bbox if bbox is not None else [0, 0, 0, 0]
        self.page_idx = page_idx
        self.id = block_id
        self.block_type = block_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'bbox': self.bbox,
            'page_idx': self.page_idx,
            'id': self.id,
            'block_type': self.block_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextBlock':
        """Create from dictionary"""
        return cls(
            text=data.get('text', ''),
            bbox=data.get('bbox', [0, 0, 0, 0]),
            page_idx=data.get('page_idx', 0),
            block_id=data.get('id', ''),
            block_type=data.get('block_type', '')
        )