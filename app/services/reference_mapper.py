from app.api.models import TextBlock, Page, Reference
from app.services.ollama_service import OllamaService
from app.config.settings import config
from typing import List, Dict, Tuple
import logging
import re
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

class ReferenceMapper:

    REFERENCE_PATTERNS =[
        # Figure
        (r'\b(?:Fig(?:ure)?s?\.?|Figure)\s*(\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?)', 'Figure'),
        
        # Table
        (r'\b(?:Tab(?:le)?s?\.?|Table)\s*(\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?)', 'Table'),
        
        # Equation
        (r'\b(?:Eq(?:uation)?s?\.?|Equation)\s*(\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?)', 'Equation'),
        (r'\((\d+(?:\.\d+)?)\)', 'Equation')
    ]
    
    # Block types that can be referenced
    REFERENCEABLE_BLOCKS = [
        'TableGroup', 'PictureGroup', 'FigureGroup', 'EquationGroup', 
        'CodeGroup', 'Picture', 'Figure', 'Equation', 'Code'
    ]

    # 병렬 처리를 위한 최소 페이지 수 임계값
    PARALLEL_PROCESSING_THRESHOLD = 100

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.use_llm = config.get_reference_mapper_config().get('use_llm')

    def map_references(self, pages: List[Page], figures: List[TextBlock]) -> List[Page]:
        try:
            # Build figure graph first (공유 데이터)
            figure_graph = self._build_figure_graph(pages, figures)
            self.logger.info("Figure graph built.")

            # 페이지 수에 따라 처리 방식 선택
            if len(pages) < self.PARALLEL_PROCESSING_THRESHOLD:
                self.logger.info(f"Using sequential processing for {len(pages)} pages")
                return self._process_pages_sequential(pages, figure_graph)
            else:
                self.logger.info(f"Using parallel processing for {len(pages)} pages")
                return self._process_pages_parallel(pages, figure_graph)

        except Exception as e:
            self.logger.error(f"Error mapping references: {e}")
            return pages

    def _process_pages_sequential(self, pages: List[Page], figure_graph: Dict[str, Dict[str, List[Dict]]]) -> List[Page]:
        """순차적으로 페이지 처리"""
        try:
            for idx, page in enumerate(pages):
                pages[idx].references = self._map_reference_per_page_static(
                    page=page,
                    figure_graph=figure_graph,
                    use_llm=self.use_llm
                )
                self.logger.info(f"References mapped for page {page.index}")
        except Exception as e:
            self.logger.error(f"Error in sequential processing: {e}")
        return pages

    def _process_pages_parallel(self, pages: List[Page], figure_graph: Dict[str, Dict[str, List[Dict]]]) -> List[Page]:
        """병렬로 페이지 처리"""
        try:
            with ProcessPoolExecutor() as executor:
                futures = []
                for page in pages:
                    future = executor.submit(
                        self._map_reference_per_page_static,
                        page=page,
                        figure_graph=figure_graph,
                        use_llm=self.use_llm
                    )
                    futures.append((page.index, future))

                for page_idx, future in futures:
                    try:
                        references = future.result()
                        for page in pages:
                            if page.index == page_idx:
                                page.references = references
                                self.logger.info(f"References mapped for page {page_idx}")
                                break
                    except Exception as e:
                        self.logger.error(f"Error processing page {page_idx}: {e}")
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {e}")
        return pages

    def _build_figure_graph(self, pages: List[Page], figures: List[TextBlock]) -> Dict[str, Dict[str, List[Dict]]]:
        """Build a graph of all referenceable blocks organized by type and number."""
        graph = {'Figure': {}, 'Table': {}, 'Equation': {}}
        
        # Process figures from the figures list
        for figure in figures:
            if figure.block_type not in self.REFERENCEABLE_BLOCKS:
                continue
                
            # Extract type and number from caption
            ref_type, number = self._extract_type_and_number_from_caption(figure.text)
            if ref_type and number:
                if number not in graph[ref_type]:
                    graph[ref_type][number] = []
                
                # Find page number for this figure
                page_num = self._find_page_number_for_block(pages, figure)
                graph[ref_type][number].append({
                    'block': figure,
                    'page': page_num,
                    'block_type': figure.block_type
                })
        
        # Also process blocks from pages
        for page in pages:
            for block in page.blocks:
                if block.block_type not in self.REFERENCEABLE_BLOCKS:
                    continue
                    
                ref_type, number = self._extract_type_and_number_from_caption(block.text)
                if ref_type and number:
                    if number not in graph[ref_type]:
                        graph[ref_type][number] = []
                    
                    # Check if this block is already in graph
                    already_exists = any(
                        item['block'].id == block.id 
                        for items in graph[ref_type][number] 
                        for item in items
                    )
                    
                    if not already_exists:
                        graph[ref_type][number].append({
                            'block': block,
                            'page': page.index,
                            'block_type': block.block_type
                        })
        
        return graph

    @staticmethod
    def _map_reference_per_page_static(page: Page, figure_graph: Dict[str, Dict[str, List[Dict]]], use_llm: bool) -> List[Reference]:
        """정적 메서드 버전의 _map_reference_per_page - 병렬 처리를 위해 필요"""
        logger = logging.getLogger(__name__)
        references = []
        
        # Ollama 서비스 초기화 (각 프로세스마다 새로운 인스턴스 필요)
        ollama_service = None
        if use_llm:
            ollama_service = OllamaService(rule='You are a helpful assistant that extracts reference text(like "Figure 9.43" or "Fig. 2.1" or "Table 1" or "Eq. 1" or "Eq. (1)" or "Code 1") from text. You will be given a text and you will need to extract the reference text from the text. The response should be in the following json format: {"reference": ["reference text"]}. just return json format, don\'t include any other text')

        for block in page.blocks:
            extracted_references = []
            if use_llm:
                try:
                    result = ollama_service.response(f'text: {block.text}')
                    if result:
                        extracted_references = json.loads(result).get('reference', [])
                except Exception as e:
                    logger.error(f"Error extracting reference text: {e}")
                    logger.error(f"result: {result}")
            else:
                # 정규식 기반 참조 추출
                for pattern, ref_type in ReferenceMapper.REFERENCE_PATTERNS:
                    match = re.search(pattern, block.text)
                    if match:
                        extracted_references.append(match.group())

            for extracted_reference in extracted_references:
                matched_figure = ReferenceMapper._find_reference_in_figures_static(
                    extracted_reference, page.index, figure_graph
                )
                if matched_figure:
                    # Get all bboxes for this reference
                    bboxes = ReferenceMapper._calculate_reference_bbox_static(extracted_reference, block)
                    # Create a Reference object for each bbox
                    for bbox in bboxes:
                        references.append(Reference(
                            text=extracted_reference,
                            bbox=bbox,
                            figure_id=matched_figure['block'].id
                        ))
                    if bboxes:
                        logger.info(f"Reference mapped: {extracted_reference} -> {matched_figure['block'].id} ({len(bboxes)} occurrences)")

        return references

    @staticmethod
    def _find_reference_in_figures_static(reference_text: str, current_page: int, figure_graph: Dict[str, Dict[str, List[Dict]]]) -> Dict:
        """정적 메서드 버전의 _find_reference_in_figures"""
        # Extract type and number from reference
        ref_type = None
        ref_number = None
        
        # Try each pattern
        for pattern, r_type in ReferenceMapper.REFERENCE_PATTERNS:
            match = re.search(pattern, reference_text)
            if match:
                ref_type = r_type
                ref_number = match.group(1)
                break
                
        if not ref_type or not ref_number:
            return None
            
        # Get candidates from graph
        if ref_type not in figure_graph or ref_number not in figure_graph[ref_type]:
            return None
            
        candidates = figure_graph[ref_type][ref_number]
        if not candidates:
            return None
            
        # If only one candidate, return it
        if len(candidates) == 1:
            return candidates[0]
            
        # Sort candidates by page distance
        def page_distance_key(item):
            page = item['page']
            if page == current_page:
                return (0, 0)  # Same page, highest priority
            elif page < current_page:
                return (1, current_page - page)  # Previous pages
            else:
                return (2, page - current_page)  # Following pages
                
        sorted_candidates = sorted(candidates, key=page_distance_key)
        return sorted_candidates[0]

    @staticmethod
    def _calculate_reference_bbox_static(reference_text: str, block: TextBlock) -> List[List[int]]:
        """정적 메서드 버전의 _calculate_reference_bbox - 여러 개의 bbox를 반환"""
        logger = logging.getLogger(__name__)
        
        if not hasattr(block, 'bbox') or not hasattr(block, 'text'):
            return []
        if not block.bbox or not block.text:
            return []

        bboxes = []
        block_x1, block_y1, block_x2, block_y2 = block.bbox
        block_width = block_x2 - block_x1
        
        print(f"[DEBUG] Block bbox: {block.bbox}, width: {block_width}")
        print(f"[DEBUG] Searching for reference: '{reference_text}' in text: '{block.text[:100]}...'")
        
        # Single line case - use the entire text
        if '\n' not in block.text:
            text = block.text
            
            # Find all occurrences in the text
            start_idx = 0
            while True:
                try:
                    rel_start = text.index(reference_text, start_idx)
                    rel_end = rel_start + len(reference_text)
                    
                    # Calculate horizontal position based on character ratio
                    text_len = len(text)
                    if text_len > 0:
                        # Use a more accurate character width estimation
                        avg_char_width = block_width / text_len
                        
                        ref_x1 = int(block_x1 + rel_start * avg_char_width)
                        ref_x2 = int(block_x1 + rel_end * avg_char_width)
                        
                        # Ensure minimum width for visibility
                        if ref_x2 - ref_x1 < 5:  # Minimum 5 pixels width
                            ref_x2 = ref_x1 + max(5, int(len(reference_text) * avg_char_width))
                        
                        print(f"[DEBUG] Single line - ref pos: {rel_start}-{rel_end}, bbox: ({ref_x1},{block_y1},{ref_x2},{block_y2})")
                        
                        # Keep the same vertical coordinates as the block
                        bboxes.append([ref_x1, block_y1, ref_x2, block_y2])
                    
                    start_idx = rel_end
                except ValueError:
                    break
            
            return bboxes

        # Multi-line case
        lines = block.text.splitlines()
        if not lines:
            return []
            
        total_height = block_y2 - block_y1
        num_lines = len(lines)
        line_height = total_height / num_lines if num_lines > 0 else 0

        # Search for the reference text in all lines
        for i, line in enumerate(lines):
            if reference_text in line:
                # Calculate Y coordinates for just this line
                ref_y1 = int(block_y1 + i * line_height)
                ref_y2 = int(block_y1 + (i + 1) * line_height)
                
                # Find all occurrences in this line
                start_idx = 0
                while True:
                    try:
                        rel_start = line.index(reference_text, start_idx)
                        rel_end = rel_start + len(reference_text)
                        
                        # Calculate X coordinates based on character position
                        line_len = len(line)
                        if line_len > 0:
                            # Use average character width for better accuracy
                            avg_char_width = block_width / line_len
                            
                            ref_x1 = int(block_x1 + rel_start * avg_char_width)
                            ref_x2 = int(block_x1 + rel_end * avg_char_width)
                            
                            # Ensure minimum width for visibility
                            if ref_x2 - ref_x1 < 5:  # Minimum 5 pixels width
                                ref_x2 = ref_x1 + max(5, int(len(reference_text) * avg_char_width))
                            
                            # Ensure coordinates are within block bounds
                            ref_x1 = max(block_x1, min(ref_x1, block_x2))
                            ref_x2 = max(block_x1, min(ref_x2, block_x2))
                            ref_y1_bounded = max(block_y1, min(ref_y1, block_y2))
                            ref_y2_bounded = max(block_y1, min(ref_y2, block_y2))
                            
                            print(f"[DEBUG] Line {i} - ref pos: {rel_start}-{rel_end}, bbox: ({ref_x1},{ref_y1_bounded},{ref_x2},{ref_y2_bounded})")
                            
                            bboxes.append([ref_x1, ref_y1_bounded, ref_x2, ref_y2_bounded])
                        
                        start_idx = rel_end
                    except ValueError:
                        break
                        
        return bboxes

    def _extract_type_and_number_from_caption(self, text: str) -> Tuple[str, str]:
        """Extract reference type and number from caption text."""
        if not text:
            return None, None
            
        # Try each pattern
        for pattern, ref_type in self.REFERENCE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                number = match.group(1)
                return ref_type, number
                
        return None, None
    
    def _find_page_number_for_block(self, pages: List[Page], target_block: TextBlock) -> int:
        """Find which page a block belongs to."""
        for page in pages:
            for block in page.blocks:
                if block.id == target_block.id:
                    return page.index
        return -1