from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from marker.renderers import BaseRenderer
from marker.renderers.json import JSONOutput
from marker.schema import BlockTypes
from marker.schema.blocks import BlockOutput
from marker.schema.document import Document
from marker.schema.registry import get_block_class


class TextLine(BaseModel):
    id: str
    text: str
    bbox: List[float]
    polygon: List[List[float]]


class LayoutBlock(BaseModel):
    """Text 블록의 Line 정보를 포함하는 확장된 JSON 출력 모델"""
    id: str
    block_type: str
    html: str
    polygon: List[List[float]]
    bbox: List[float]
    children: List['LayoutBlock'] | None = None
    section_hierarchy: Dict[int, str] | None = None
    images: dict | None = None
    lines: Optional[List[TextLine]] = None  # Line 정보 추가

class DocumentLayoutOutput(BaseModel):
    pages: List[LayoutBlock]
    block_type: str = str(BlockTypes.Document)


class LayoutRenderer(BaseRenderer):
    """Text 블록의 Line 정보를 보존하는 레이아웃 렌더러"""
    
    def extract_layout(self, document: Document, block_output: BlockOutput) -> LayoutBlock:
        """블록을 LayoutBlock으로 변환"""
        # Block 클래스 가져오기
        cls = get_block_class(block_output.id.block_type)
        
        # 기본 블록 타입인 경우 (Text, Caption 등)
        if cls.__base__.__name__ == "Block":
            html, images = self.extract_block_html(document, block_output)
            
            # 기본 출력 생성
            layout_block = LayoutBlock(
                html=html,
                polygon=block_output.polygon.polygon,
                bbox=block_output.polygon.bbox,
                id=str(block_output.id),
                block_type=str(block_output.id.block_type),
                images=images,
                section_hierarchy=self._reformat_section_hierarchy(block_output.section_hierarchy)
            )
            
            # Text 블록인 경우 Line 정보 추가
            if block_output.id.block_type in [BlockTypes.Text, BlockTypes.TextInlineMath]:
                lines = []
                
                # Document에서 실제 블록 가져오기
                text_block = document.get_block(block_output.id)
                if text_block and text_block.structure:
                    # Line 블록들 가져오기
                    for line_id in text_block.structure:
                        if line_id.block_type == BlockTypes.Line:
                            line_block = document.get_block(line_id)
                            if line_block:
                                # Line의 raw text 가져오기
                                line_text = line_block.raw_text(document).strip()
                                
                                lines.append(TextLine(
                                    id=str(line_id),
                                    text=line_text,
                                    bbox=line_block.polygon.bbox,
                                    polygon=line_block.polygon.polygon
                                ))
                
                layout_block.lines = lines
            
            return layout_block
        
        # Group 타입인 경우 (Page, TableGroup 등)
        else:
            children = []
            for child in block_output.children:
                child_output = self.extract_layout(document, child)
                children.append(child_output)
            
            return LayoutBlock(
                html=block_output.html,
                polygon=block_output.polygon.polygon,
                bbox=block_output.polygon.bbox,
                id=str(block_output.id),
                block_type=str(block_output.id.block_type),
                children=children,
                section_hierarchy=self._reformat_section_hierarchy(block_output.section_hierarchy)
            )
    
    def _reformat_section_hierarchy(self, section_hierarchy):
        if not section_hierarchy:
            return None
        new_section_hierarchy = {}
        for key, value in section_hierarchy.items():
            new_section_hierarchy[key] = str(value)
        return new_section_hierarchy
    
    def __call__(self, document: Document) -> DocumentLayoutOutput:
        document_output = document.render()
        
        layout_pages = []
        for page_output in document_output.children:
            layout_pages.append(self.extract_layout(document, page_output))
        
        return DocumentLayoutOutput(
            pages=layout_pages,
            block_type=str(BlockTypes.Document)
        )