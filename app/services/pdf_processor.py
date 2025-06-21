import fitz  # PyMuPDF
import logging
import tempfile
import os
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
import gc

from app.config.settings import config


class PDFProcessor:
    """
    PDF processing service using PyMuPDF (fitz) for document analysis.
    Optimized for large PDF processing with memory management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_files = []  # Track temporary files for cleanup
        
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata including document information
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata information
        """
        try:
            doc = fitz.open(pdf_path)
            
            # Basic metadata
            metadata = {
                'filename': os.path.basename(pdf_path),
                'total_pages': doc.page_count,
                'file_size': os.path.getsize(pdf_path),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'format': doc.metadata.get('format', 'PDF'),
                'encryption': doc.metadata.get('encryption', None),
                'pages_info': []
            }
            
            # Extract page-level information
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_info = {
                    'page_number': page_num + 1,
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'rotation': page.rotation
                }
                metadata['pages_info'].append(page_info)
            
            doc.close()
            
            self.logger.info(f"Extracted metadata for {metadata['filename']}: {metadata['total_pages']} pages")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {str(e)}")
            raise
    
    def extract_pages_as_images(self, pdf_path: str, dpi: int = 200, 
                               start_page: Optional[int] = None, 
                               end_page: Optional[int] = None) -> List[Image.Image]:
        """
        Extract PDF pages as high-resolution images
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for image conversion (default 200 for good quality)
            start_page: Starting page number (0-indexed), None for first page
            end_page: Ending page number (0-indexed), None for last page
            
        Returns:
            List of PIL Images for each page
        """
        images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count
            
            # Determine page range
            if start_page is None:
                start_page = 0
            if end_page is None:
                end_page = total_pages - 1
                
            # Validate page range
            start_page = max(0, min(start_page, total_pages - 1))
            end_page = max(start_page, min(end_page, total_pages - 1))
            
            self.logger.info(f"Extracting pages {start_page + 1} to {end_page + 1} from {pdf_path}")
            
            # Calculate matrix for desired DPI
            # PyMuPDF default is 72 DPI, so scale factor = desired_dpi / 72
            scale_factor = dpi / 72.0
            matrix = fitz.Matrix(scale_factor, scale_factor)
            
            for page_num in range(start_page, end_page + 1):
                try:
                    page = doc[page_num]
                    
                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("ppm")
                    img = Image.open(fitz.io.BytesIO(img_data))
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    images.append(img)
                    
                    # Clean up pixmap
                    pix = None
                    
                    # Memory management for large documents
                    if (page_num - start_page + 1) % 50 == 0:  # Every 50 pages
                        gc.collect()
                        self.logger.info(f"Processed {page_num - start_page + 1} pages, running garbage collection")
                    
                except Exception as e:
                    self.logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                    # Continue with next page instead of failing completely
                    continue
            
            self.logger.info(f"Successfully extracted {len(images)} pages as images")
            return images
            
        except Exception as e:
            self.logger.error(f"Error extracting images from {pdf_path}: {str(e)}")
            raise
        finally:
            if doc:
                doc.close()
            gc.collect()
    
    def get_page_info(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Get detailed information for each page
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with page information
        """
        try:
            doc = fitz.open(pdf_path)
            pages_info = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Get text statistics
                text = page.get_text()
                word_count = len(text.split()) if text else 0
                char_count = len(text) if text else 0
                
                # Get image count
                image_list = page.get_images()
                image_count = len(image_list)
                
                # Get drawing/vector graphics info
                drawings = page.get_drawings()
                drawing_count = len(drawings)
                
                page_info = {
                    'page_number': page_num + 1,
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'rotation': page.rotation,
                    'word_count': word_count,
                    'char_count': char_count,
                    'image_count': image_count,
                    'drawing_count': drawing_count,
                    'has_text': word_count > 0,
                    'has_images': image_count > 0,
                    'has_drawings': drawing_count > 0
                }
                
                pages_info.append(page_info)
            
            doc.close()
            return pages_info
            
        except Exception as e:
            self.logger.error(f"Error getting page info from {pdf_path}: {str(e)}")
            raise
    
    def extract_text_with_coordinates(self, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text with coordinate information for a specific page
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            List of text blocks with coordinates
        """
        try:
            doc = fitz.open(pdf_path)
            
            if page_num >= doc.page_count:
                raise ValueError(f"Page {page_num + 1} not found in document")
            
            page = doc[page_num]
            
            # Get text blocks with coordinates
            text_blocks = []
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:  # Text block
                    block_text = ""
                    bbox = block["bbox"]  # (x0, y0, x1, y1)
                    
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"]
                    
                    if block_text.strip():
                        text_blocks.append({
                            'text': block_text.strip(),
                            'bbox': bbox,
                            'page_number': page_num + 1
                        })
            
            doc.close()
            return text_blocks
            
        except Exception as e:
            self.logger.error(f"Error extracting text with coordinates: {str(e)}")
            raise
    
    def process_in_batches(self, pdf_path: str, batch_size: int = 50) -> List[Image.Image]:
        """
        Process large PDFs in batches to manage memory usage
        
        Args:
            pdf_path: Path to the PDF file
            batch_size: Number of pages to process at once
            
        Returns:
            List of all page images
        """
        metadata = self.extract_metadata(pdf_path)
        total_pages = metadata['total_pages']
        
        self.logger.info(f"Processing {total_pages} pages in batches of {batch_size}")
        
        all_images = []
        
        for start_page in range(0, total_pages, batch_size):
            end_page = min(start_page + batch_size - 1, total_pages - 1)
            
            self.logger.info(f"Processing batch: pages {start_page + 1} to {end_page + 1}")
            
            batch_images = self.extract_pages_as_images(
                pdf_path, 
                start_page=start_page, 
                end_page=end_page
            )
            
            all_images.extend(batch_images)
            
            # Force garbage collection between batches
            gc.collect()
        
        return all_images
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files created during processing"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                self.logger.warning(f"Could not delete temporary file {temp_file}: {str(e)}")
        
        self.temp_files.clear()
        self.logger.info("Temporary files cleaned up")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_temp_files()