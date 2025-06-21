"""
AnalysisResponse data model
"""
from typing import List, Dict, Any
from .metadata import Metadata
from .page import Page
from .text_block import TextBlock

class AnalysisResponse:
    """Analysis response data model"""
    
    def __init__(self, metadata: Metadata = None, pages: List[Page] = None, figures: List[TextBlock] = None):
        self.metadata = metadata if metadata is not None else Metadata()
        self.pages = pages if pages is not None else []
        self.figures = figures if figures is not None else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metadata': self.metadata.to_dict(),
            'pages': [page.to_dict() for page in self.pages],
            'figures': [figure.to_dict() for figure in self.figures]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResponse':
        """Create from dictionary"""
        metadata = Metadata.from_dict(data.get('metadata', {}))
        pages = [Page.from_dict(page_data) for page_data in data.get('pages', [])]
        figures = [TextBlock.from_dict(figure_data) for figure_data in data.get('figures', [])]
        return cls(metadata=metadata, pages=pages, figures=figures)