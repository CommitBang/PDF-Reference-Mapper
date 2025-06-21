#!/usr/bin/env python3
"""
Test script for Marker with Ollama integration
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.marker_ocr_service import MarkerOCRService
from app.config.settings import config


def test_ollama_integration():
    """Test Marker OCR with Ollama LLM service"""
    
    print("Testing Marker with Ollama integration...")
    
    # Initialize service
    marker_service = MarkerOCRService()
    
    # Check Ollama configuration
    ollama_config = config.get_llm_service_config('ollama')
    print(f"\nOllama Configuration:")
    print(f"  - Enabled: {ollama_config.get('enabled', False)}")
    print(f"  - Base URL: {ollama_config.get('base_url', 'http://localhost:11434')}")
    print(f"  - Model: {ollama_config.get('model', 'llama2')}")
    
    # Check if Ollama is accessible
    if marker_service.check_ollama_service():
        print("\n✅ Ollama service is accessible")
    else:
        print("\n❌ Ollama service is not accessible")
        print("   Please make sure Ollama is running with: ollama serve")
        
    # Initialize models
    try:
        marker_service.initialize_model()
        print("\n✅ Marker models initialized successfully")
        
        if marker_service.llm_service:
            print("✅ Ollama LLM service integrated with Marker")
        else:
            print("⚠️  Marker initialized without LLM support")
            
    except Exception as e:
        print(f"\n❌ Failed to initialize Marker: {str(e)}")
        return
    
    # Test with a sample PDF if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if os.path.exists(pdf_path):
            print(f"\nProcessing PDF: {pdf_path}")
            try:
                markdown_text, metadata, images = marker_service.process_pdf_file(pdf_path)
                print(f"\n✅ PDF processed successfully")
                print(f"   - Text length: {len(markdown_text)} characters")
                print(f"   - Metadata items: {len(metadata)}")
                print(f"   - Images extracted: {len(images)}")
                
                # Show first 500 characters of extracted text
                print(f"\nFirst 500 characters of extracted text:")
                print("-" * 50)
                print(markdown_text[:500])
                print("-" * 50)
                
            except Exception as e:
                print(f"\n❌ Failed to process PDF: {str(e)}")
        else:
            print(f"\n❌ PDF file not found: {pdf_path}")
    else:
        print("\nNo PDF file provided. Usage: python test_ollama_marker.py <pdf_path>")


if __name__ == "__main__":
    test_ollama_integration()