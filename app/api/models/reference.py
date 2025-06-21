from typing import List, Dict, Any, Optional


class Reference:
    """Reference data model for figure/table/equation references in text"""
    
    def __init__(self, text: str = "", bbox: List[float] = None, 
                 figure_id: Optional[str] = None, not_matched: bool = False):
        self.text = text
        self.bbox = bbox if bbox is not None else [0, 0, 0, 0]
        self.figure_id = figure_id
        self.not_matched = not_matched
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'bbox': self.bbox,
            'figure_id': self.figure_id,
            'not_matched': self.not_matched
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reference':
        """Create from dictionary"""
        return cls(
            text=data.get('text', ''),
            bbox=data.get('bbox', [0, 0, 0, 0]),
            figure_id=data.get('figure_id'),
            not_matched=data.get('not_matched', False)
        )