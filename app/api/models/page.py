"""
Page data model
"""
from typing import List, Dict, Any
from .text_block import TextBlock
from .reference import Reference


class Page:
    """Page data model"""
    
    def __init__(self, index: int = 0, page_size: List[int] = None, 
                 blocks: List[TextBlock] = None, references: List[Reference] = None):
        self.index = index
        self.page_size = page_size if page_size is not None else [0, 0]
        self.blocks = blocks if blocks is not None else []
        self.references = references if references is not None else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'index': self.index,
            'page_size': self.page_size,
            'blocks': [block.to_dict() for block in self.blocks],
            'references': [ref.to_dict() for ref in self.references]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """Create from dictionary"""
        blocks = [TextBlock.from_dict(block_data) for block_data in data.get('blocks', [])]
        references = [Reference.from_dict(ref_data) for ref_data in data.get('references', [])]
        return cls(
            index=data.get('index', 0),
            page_size=data.get('page_size', [0, 0]),
            blocks=blocks,
            references=references
        )