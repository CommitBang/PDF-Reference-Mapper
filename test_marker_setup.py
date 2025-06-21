#!/usr/bin/env python3
"""
Test script for Marker OCR implementation
Verifies that the system can load models and process basic functionality
"""

import sys
import os
import logging
import tempfile
from pathlib import Path

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config.settings import config
from app.services.marker_ocr_service import MarkerOCRService, TextBlock, MARKER_AVAILABLE
from app.services.pdf_processor import PDFProcessor
from app.utils.gpu_utils import gpu_manager
from app.utils.file_utils import ImagePreprocessor


def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        # Test config loading
        marker_config = config.get_model_config('marker')
        hardware_config = config.get_hardware_config()
        
        print(f"✅ Marker GPU memory: {marker_config.get('gpu_memory', 'Not specified')}GB")
        print(f"✅ Device: {marker_config.get('device', 'Not specified')}")
        print(f"✅ Output format: {marker_config.get('output_format', 'Not specified')}")
        print(f"✅ Total GPU memory: {hardware_config.get('total_gpu_memory', 'Not specified')}GB")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


def test_marker_availability():
    """Test Marker library availability"""
    print("\n📚 Testing Marker library availability...")
    
    try:
        if not MARKER_AVAILABLE:
            print("❌ Marker library is not available")
            print("💡 Install with: pip install marker-pdf[full]")
            return False
        
        # Try importing specific components
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        
        print("✅ Marker library is available")
        print("✅ All required components can be imported")
        
        return True
    except ImportError as e:
        print(f"❌ Marker import failed: {str(e)}")
        print("💡 Install with: pip install marker-pdf[full]")
        return False
    except Exception as e:
        print(f"❌ Marker test failed: {str(e)}")
        return False


def test_gpu_setup():
    """Test GPU availability and memory management"""
    print("\n🚀 Testing GPU setup...")
    
    try:
        # Check GPU availability
        memory_info = gpu_manager.check_gpu_memory()
        
        if memory_info.get('available', False):
            print(f"✅ GPU available: {memory_info['total']}GB total")
            print(f"✅ Free memory: {memory_info['free']}GB")
            print(f"✅ Memory utilization: {memory_info['utilization']}%")
        else:
            print("⚠️  GPU not available - will use CPU")
            
        # Test memory allocation
        can_allocate = gpu_manager.allocate_model_memory('marker')
        print(f"✅ Can allocate Marker memory: {can_allocate}")
        
        return True
    except Exception as e:
        print(f"❌ GPU setup test failed: {str(e)}")
        return False


def test_marker_model_loading():
    """Test Marker model initialization"""
    print("\n🤖 Testing Marker model loading...")
    
    try:
        if not MARKER_AVAILABLE:
            print("❌ Marker not available, skipping model test")
            return False
        
        ocr_service = MarkerOCRService()
        
        print("📥 Initializing Marker models (this may take a few minutes on first run)...")
        ocr_service.initialize_model()
        
        print("✅ Marker models loaded successfully!")
        print(f"✅ Converter initialized: {ocr_service.converter is not None}")
        print(f"✅ Model dict loaded: {ocr_service.model_dict is not None}")
        
        # Cleanup
        ocr_service.cleanup_resources()
        print("✅ Model cleanup successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Try: pip install marker-pdf[full]")
        return False
    except Exception as e:
        print(f"❌ Marker model test failed: {str(e)}")
        
        # Check if it's an OOM error
        if "out of memory" in str(e).lower():
            print("💡 This appears to be a GPU memory issue.")
            print("💡 Try reducing GPU memory allocation or use CPU-only mode")
        
        return False


def test_pdf_processor():
    """Test PDF processor without actual PDF"""
    print("\n📄 Testing PDF processor...")
    
    try:
        pdf_processor = PDFProcessor()
        print("✅ PDF processor initialized successfully")
        
        # Test utility functions
        pdf_processor.cleanup_temp_files()
        print("✅ Temp file cleanup function works")
        
        return True
    except Exception as e:
        print(f"❌ PDF processor test failed: {str(e)}")
        return False


def test_text_block_processing():
    """Test text block processing with sample data"""
    print("\n📝 Testing text block processing...")
    
    try:
        if not MARKER_AVAILABLE:
            print("⚠️  Marker not available, testing basic text processing only")
            
            # Test TextBlock creation
            sample_block = TextBlock(
                text="Sample text block",
                bbox=(100, 100, 200, 50),
                confidence=0.95,
                page_idx=0,
                block_type="text"
            )
            print("✅ TextBlock creation successful")
            return True
        
        ocr_service = MarkerOCRService()
        
        # Test markdown processing
        sample_markdown = """# Sample Document
        
This is a test paragraph with some content.

## Section 2

- List item 1
- List item 2

Another paragraph here."""
        
        # Test text block extraction from markdown
        text_blocks = ocr_service.extract_text_blocks_from_markdown(
            sample_markdown, [], None
        )
        
        print(f"✅ Text block extraction successful: {len(text_blocks)} blocks")
        
        for i, block in enumerate(text_blocks[:3]):  # Show first 3 blocks
            print(f"   Block {i+1}: {block.block_type} - {block.text[:30]}...")
        
        return True
    except Exception as e:
        print(f"❌ Text block processing test failed: {str(e)}")
        return False


def test_image_preprocessing():
    """Test image preprocessing utilities"""
    print("\n🖼️  Testing image preprocessing...")
    
    try:
        preprocessor = ImagePreprocessor()
        print("✅ Image preprocessor initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ Image preprocessing test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🧪 PDF Mapper - Marker OCR Implementation Test")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress some verbose logs for cleaner output
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    
    tests = [
        ("Configuration", test_configuration),
        ("Marker Library", test_marker_availability),
        ("GPU Setup", test_gpu_setup),
        ("PDF Processor", test_pdf_processor),
        ("Image Preprocessing", test_image_preprocessing),
        ("Text Block Processing", test_text_block_processing),
        ("Marker Model Loading", test_marker_model_loading),  # Most intensive test last
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The Marker OCR implementation is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("💡 Common issues:")
        print("   - Missing Marker: pip install marker-pdf[full]")
        print("   - GPU memory: Reduce gpu_memory in config.yaml")
        print("   - CUDA setup: Ensure CUDA is properly installed")
    
    print("\n🚀 To start the server: python -m app.main")
    print("📚 API docs will be available at: http://localhost:5000/docs/")


if __name__ == "__main__":
    main()