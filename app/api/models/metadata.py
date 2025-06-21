"""
Metadata data model
"""
from typing import List, Optional, Dict, Any


class Metadata:
    """Metadata data model"""
    
    def __init__(self, filename: str = "", total_pages: int = 0, file_size: int = 0, 
                 processing_time: float = 0.0, processor: str = "marker",
                 table_of_contents: Optional[List[Dict[str, Any]]] = None,
                 page_stats: Optional[List[Dict[str, Any]]] = None):
        self.filename = filename
        self.total_pages = total_pages
        self.file_size = file_size
        self.processing_time = round(processing_time, 2)
        self.processor = processor
        self.table_of_contents = table_of_contents
        self.page_stats = page_stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'filename': self.filename,
            'total_pages': self.total_pages,
            'file_size': self.file_size,
            'processing_time': self.processing_time,
            'processor': self.processor
        }
        if self.table_of_contents is not None:
            result['table_of_contents'] = self.table_of_contents
        if self.page_stats is not None:
            result['page_stats'] = self.page_stats
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        """Create from dictionary"""
        return cls(
            filename=data.get('filename', ''),
            total_pages=data.get('total_pages', 0),
            file_size=data.get('file_size', 0),
            processing_time=data.get('processing_time', 0.0),
            processor=data.get('processor', 'marker'),
            table_of_contents=data.get('table_of_contents'),
            page_stats=data.get('page_stats')
        )