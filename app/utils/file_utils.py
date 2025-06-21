import cv2
import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Tuple, Optional
import logging

from app.config.settings import config


class ImagePreprocessor:
    """
    Image preprocessing utilities using OpenCV for PDF page enhancement.
    Optimized for OCR and computer vision model input preparation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hardware_config = config.get_hardware_config()
        
    def preprocess_image(self, image: Image.Image, enhance_for_ocr: bool = True) -> np.ndarray:
        """
        Preprocess image for better OCR and analysis results
        
        Args:
            image: PIL Image to preprocess
            enhance_for_ocr: Whether to apply OCR-specific enhancements
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Apply preprocessing pipeline
            if enhance_for_ocr:
                img_array = self._enhance_for_ocr(img_array)
            else:
                img_array = self._basic_enhancement(img_array)
            
            return img_array
            
        except Exception as e:
            self.logger.error(f"Error in image preprocessing: {str(e)}")
            raise
    
    def _enhance_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """Apply OCR-specific enhancements"""
        # Convert to grayscale for text processing
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Sharpen text
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to 3-channel for consistency
        if len(sharpened.shape) == 2:
            sharpened = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
        
        return sharpened
    
    def _basic_enhancement(self, img: np.ndarray) -> np.ndarray:
        """Apply basic image enhancements"""
        # Noise reduction
        denoised = cv2.bilateralFilter(img, 9, 75, 75)
        
        # Slight sharpening
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]])
        enhanced = cv2.filter2D(denoised, -1, kernel)
        
        return enhanced
    
    def normalize_image_batch(self, images: List[Image.Image], target_size: Optional[Tuple[int, int]] = None) -> torch.Tensor:
        """
        Normalize a batch of images for deep learning models
        
        Args:
            images: List of PIL Images
            target_size: Target size (width, height), None to keep original
            
        Returns:
            Normalized tensor batch
        """
        try:
            processed_images = []
            
            for image in images:
                # Resize if target size specified
                if target_size:
                    image = image.resize(target_size, Image.Resampling.LANCZOS)
                
                # Convert to array and normalize
                img_array = np.array(image).astype(np.float32)
                
                # Normalize to [0, 1]
                img_array = img_array / 255.0
                
                # Add to batch
                processed_images.append(img_array)
            
            # Convert to tensor
            batch_tensor = torch.tensor(np.stack(processed_images))
            
            # Rearrange dimensions from (B, H, W, C) to (B, C, H, W)
            if len(batch_tensor.shape) == 4:
                batch_tensor = batch_tensor.permute(0, 3, 1, 2)
            
            return batch_tensor
            
        except Exception as e:
            self.logger.error(f"Error normalizing image batch: {str(e)}")
            raise
    
    def enhance_text_clarity(self, image: Image.Image) -> Image.Image:
        """
        Enhance text clarity specifically for OCR processing
        
        Args:
            image: PIL Image containing text
            
        Returns:
            Enhanced PIL Image
        """
        try:
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.2)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.1)
            
            # Slight brightness adjustment if needed
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.05)
            
            # Apply unsharp mask filter
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing text clarity: {str(e)}")
            return image  # Return original if enhancement fails
    
    def prepare_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Prepare image specifically for Nougat OCR input
        
        Args:
            image: PIL Image to prepare
            
        Returns:
            OCR-ready PIL Image
        """
        try:
            # Ensure RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply text clarity enhancement
            enhanced = self.enhance_text_clarity(image)
            
            # Convert to OpenCV for advanced processing
            cv_img = np.array(enhanced)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
            
            # Apply OCR-specific preprocessing
            processed = self._enhance_for_ocr(cv_img)
            
            # Convert back to PIL
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            result = Image.fromarray(processed)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error preparing image for OCR: {str(e)}")
            return image  # Return original if preparation fails
    
    def prepare_for_yolo(self, image: Image.Image, input_size: int = 640) -> Image.Image:
        """
        Prepare image for YOLOv8 input
        
        Args:
            image: PIL Image to prepare
            input_size: Target input size for YOLO (default 640)
            
        Returns:
            YOLO-ready PIL Image
        """
        try:
            # Calculate resize dimensions maintaining aspect ratio
            width, height = image.size
            scale = min(input_size / width, input_size / height)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize image
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create new image with target size and paste resized image
            result = Image.new('RGB', (input_size, input_size), (114, 114, 114))  # Gray padding
            
            # Calculate paste position (center)
            paste_x = (input_size - new_width) // 2
            paste_y = (input_size - new_height) // 2
            
            result.paste(resized, (paste_x, paste_y))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error preparing image for YOLO: {str(e)}")
            return image
    
    def batch_preprocess(self, images: List[Image.Image], target_format: str = 'ocr') -> List[Image.Image]:
        """
        Preprocess a batch of images efficiently
        
        Args:
            images: List of PIL Images
            target_format: 'ocr', 'yolo', or 'basic'
            
        Returns:
            List of preprocessed PIL Images
        """
        processed_images = []
        
        for i, image in enumerate(images):
            try:
                if target_format == 'ocr':
                    processed = self.prepare_for_ocr(image)
                elif target_format == 'yolo':
                    processed = self.prepare_for_yolo(image)
                else:  # basic
                    enhanced_array = self.preprocess_image(image, enhance_for_ocr=False)
                    processed = Image.fromarray(cv2.cvtColor(enhanced_array, cv2.COLOR_BGR2RGB))
                
                processed_images.append(processed)
                
            except Exception as e:
                self.logger.warning(f"Failed to preprocess image {i}: {str(e)}, using original")
                processed_images.append(image)
        
        return processed_images