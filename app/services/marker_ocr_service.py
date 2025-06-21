import os
import tempfile
import logging
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import re
import gc
from pathlib import Path
import requests

from app.api.models import TextBlock, Page
from app.config.settings import config
from app.services.marker_pdf_converter import MarkerPDFConverter, ProgressCallback
from app.utils.marker_utils import extract_text_from_html

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.services.ollama import OllamaService
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

class MarkerOCRResult:
    def __init__(self, pages: List[Page], figures: List[TextBlock]):
        self.pages = pages
        self.figures = figures

class MarkerOCRService:
    """
    OCR service using Marker library for PDF-to-Markdown conversion with progress callbacks.
    """
    
    def __init__(self, progress_callback: Optional[ProgressCallback] = None):
        self.logger = logging.getLogger(__name__)
        self.model_config = config.get_model_config('marker')
        self.ollama_config = config.get_llm_service_config('ollama')
        self.progress_callback = progress_callback
        self.converter = None
        self._initialize_converter()
        
        if not MARKER_AVAILABLE:
            raise ImportError("Marker library is not available. Install with: pip install marker-pdf[full]")
        
    def _initialize_converter(self):
        """MarkerPDFConverter를 사용하여 초기화"""
        self.converter = MarkerPDFConverter(progress_callback=self.progress_callback)

    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running and accessible"""
        if not self.ollama_config.get('enabled', False):
            return False
        
        try:
            base_url = self.ollama_config.get('base_url', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama service is accessible")
                return True
        except Exception as e:
            self.logger.warning(f"Ollama service not accessible: {str(e)}")
        
        return False
    
    def _group_figures(self, figures: List[TextBlock]) -> List[TextBlock]:
        group_types = ['FigureGroup', 'TableGroup', 'PictureGroup']
        target_map = {
            'Figure': 'FigureGroup',
            'Picture': 'PictureGroup',
            'Table': 'TableGroup',
            'Code': 'CodeGroup',
            'Equation': 'EquationGroup'
        }
        grouped: List[TextBlock] = [f for f in figures if f.block_type in group_types]
        figures_only = [f for f in figures if f.block_type in target_map]
        captions = [f for f in figures if f.block_type == 'Caption']
        used_caption_ids = set()

        def bbox_distance(b1, b2):
            # 중심점 거리 (y축 우선)
            cx1, cy1 = (b1[0]+b1[2])/2, (b1[1]+b1[3])/2
            cx2, cy2 = (b2[0]+b2[2])/2, (b2[1]+b2[3])/2
            return abs(cy1-cy2) + abs(cx1-cx2)

        def merge_bbox(b1, b2):
            x0 = min(b1[0], b2[0])
            y0 = min(b1[1], b2[1])
            x1 = max(b1[2], b2[2])
            y1 = max(b1[3], b2[3])
            return [x0, y0, x1, y1]

        for fig in figures_only:
            candidates = [c for c in captions if c.page_idx == fig.page_idx and c.id not in used_caption_ids]
            if not candidates:
                grouped.append(fig)
                continue
            # 거리순 정렬, threshold=100(픽셀) 이내만 허용
            candidates = sorted(candidates, key=lambda c: bbox_distance(fig.bbox, c.bbox))
            caption = None
            for c in candidates:
                if bbox_distance(fig.bbox, c.bbox) < 200:  # threshold
                    caption = c
                    break
            if caption:
                used_caption_ids.add(caption.id)
                merged_bbox = merge_bbox(fig.bbox, caption.bbox)
                grouped.append(TextBlock(
                    text=caption.text,
                    bbox=merged_bbox,
                    page_idx=fig.page_idx,
                    block_id=caption.id,
                    block_type=target_map[fig.block_type]
                ))
            else:
                grouped.append(fig)
        return grouped

    def add_progress_callback(self, callback):
        """진행상황 콜백 추가"""
        if self.converter:
            self.converter.add_progress_callback(callback)
    
    def remove_progress_callback(self, callback):
        """진행상황 콜백 제거"""
        if self.converter:
            self.converter.remove_progress_callback(callback)
    
    def process_pdf(self, pdf_path: str) -> MarkerOCRResult:
        figure_types = ['Figure', 'Picture', 'Table', 'Caption', 'Code', 'Equation']
        if self.converter is None:
            self._initialize_converter()
        try:
            self.logger.info(f"Processing PDF to JSON with Marker: {pdf_path}")
            json_output = self.converter(pdf_path)
            all_pages: Dict[int, Page] = {}
            all_figures: List[TextBlock] = []
            block_ids = set()
            stack = []
            page_idx = 0
            for block in json_output.pages:
                if block.block_type == 'Page':
                    stack.append((block, page_idx))
                    page_idx += 1
            while stack:
                block, current_page_idx = stack.pop()
                if getattr(block, 'id', None) in block_ids:
                    continue
                block_ids.add(getattr(block, 'id', None))
                if block.block_type == 'Page':
                    page_bbox = block.bbox
                    page_width = page_bbox[2] if len(page_bbox) >= 3 else 612
                    page_height = page_bbox[3] if len(page_bbox) >= 4 else 792
                    page = Page(
                        index=current_page_idx,
                        page_size=[int(page_width), int(page_height)],
                        blocks=[]
                    )
                    all_pages[current_page_idx] = page
                    if hasattr(block, 'children') and block.children:
                        for child in block.children:
                            stack.append((child, current_page_idx))
                elif block.block_type in ['FigureGroup', 'TableGroup', 'PictureGroup']:
                    figure_text = ''
                    if hasattr(block, 'children') and block.children:
                        for child in block.children:
                            block_ids.add(getattr(child, 'id', None))
                            if child.block_type == 'Caption':
                                figure_text = extract_text_from_html(child.html)
                                break
                    text_block = TextBlock(
                        text=figure_text,
                        bbox=block.bbox if isinstance(block.bbox, list) else [0, 0, 0, 0],
                        page_idx=current_page_idx,
                        block_id=block.id,
                        block_type=block.block_type
                    )
                    all_figures.append(text_block)
                elif block.block_type == 'Text' or block.block_type == 'TextInlineMath':
                    for line in block.lines:
                        text_block = TextBlock(
                            text=line.text,
                            bbox=line.bbox,
                            page_idx=current_page_idx,
                            block_id=line.id,
                            block_type=block.block_type
                        )
                        all_pages[current_page_idx].blocks.append(text_block)
                elif block.block_type != 'ListGroup':
                    text_block = TextBlock(
                        text=extract_text_from_html(block.html),
                        bbox=block.bbox if isinstance(block.bbox, list) else [0, 0, 0, 0],
                        page_idx=current_page_idx,
                        block_id=block.id,
                        block_type=block.block_type
                    )
                    if block.block_type in figure_types:
                        all_figures.append(text_block)
                    elif current_page_idx in all_pages:
                        all_pages[current_page_idx].blocks.append(text_block) # Add text block (not figure)
                    if hasattr(block, 'children') and block.children:
                        for child in block.children:
                            stack.append((child, current_page_idx))
            self.logger.info(f"Marker JSON processing complete. Generated {len(all_pages)} pages")
            
            sorted_pages = sorted(all_pages.values(), key=lambda p: p.index)
            return MarkerOCRResult(sorted_pages, self._group_figures(all_figures))
        except Exception as e:
            self.logger.error(f"Error processing PDF to JSON with Marker: {str(e)}")
            raise

    def cleanup_resources(self) -> None:
        """Clean up model resources"""
        try:
            self.converter = None
            gc.collect()
            self.logger.info("Marker resources cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error cleaning up resources: {str(e)}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_resources()