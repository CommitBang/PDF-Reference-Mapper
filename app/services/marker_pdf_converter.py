import logging
import time
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path
import gc

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.util import classes_to_strings
from marker.providers.registry import provider_from_filepath
from marker.builders.document import DocumentBuilder
from marker.builders.layout import LayoutBuilder
from marker.builders.line import LineBuilder
from marker.builders.ocr import OcrBuilder
from marker.builders.structure import StructureBuilder
        

from app.services.layout_rendere import LayoutRenderer
from app.config.settings import config

layout_renderer_path = classes_to_strings([LayoutRenderer])[0]


class ProgressCallback:
    """콜백 함수들을 관리하는 클래스"""
    
    def __init__(self):
        self.callbacks: List[Callable[[str, int, int, Dict[str, Any]], None]] = []
    
    def add_callback(self, callback: Callable[[str, int, int, Dict[str, Any]], None]):
        """진행상황 업데이트 콜백 함수 추가
        
        Args:
            callback: (processor_name, current_index, total_processors, extra_info) -> None 형태의 함수
        """
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, int, int, Dict[str, Any]], None]):
        """콜백 함수 제거"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def notify(self, processor_name: str, current: int, total: int, extra_info: Dict[str, Any] = None):
        """모든 등록된 콜백에 진행상황 알림"""
        for callback in self.callbacks:
            try:
                callback(processor_name, current, total, extra_info or {})
            except Exception as e:
                logging.getLogger(__name__).warning(f"Callback error: {e}")


class MarkerPDFConverter(PdfConverter):
    """
    Marker의 PdfConverter를 상속받아 각 processor 실행 시마다 콜백 기능을 추가한 PDF 변환기
    """
    
    def __init__(self, progress_callback: Optional[ProgressCallback] = None, **kwargs):
        """
        Args:
            progress_callback: 각 processor 실행 시 호출될 콜백 객체
            **kwargs: PdfConverter에 전달할 추가 인자들
        """
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback or ProgressCallback()
        
        # 기본 설정 로드
        model_config = config.get_model_config('marker')
        ollama_config = config.get_llm_service_config('ollama')
        
        # Marker 모델 초기화
        model_dict = create_model_dict()
        
        # 설정 구성
        marker_config = {
            "output_format": "json", 
            'disable_image_extraction': True
        }
        
        # Ollama 설정 (사용 가능한 경우)
        if ollama_config.get('enabled', False) and self._check_ollama_service(ollama_config):
            self.logger.info("Configuring Ollama LLM service...")
            marker_config.update({
                "use_llm": True,
                "llm_service": "marker.services.ollama.OllamaService",
                "ollama_base_url": ollama_config.get('base_url', 'http://localhost:11434'),
                "ollama_model": ollama_config.get('model', 'llama2')
            })
        
        # 사용자 정의 설정 적용
        if kwargs.get('config'):
            marker_config.update(kwargs['config'])
        
        # ConfigParser 생성
        config_parser = ConfigParser(marker_config)
        
        # PdfConverter 초기화
        super().__init__(
            config=config_parser.generate_config_dict(),
            artifact_dict=model_dict,
            processor_list=config_parser.get_processors(),
            renderer=layout_renderer_path,
            llm_service=config_parser.get_llm_service(),
            **{k: v for k, v in kwargs.items() if k != 'config'}
        )
        
        self.logger.info(f"MarkerPDFConverter initialized with {len(self.processor_list)} processors")
    
    def _check_ollama_service(self, ollama_config: Dict[str, Any]) -> bool:
        """Ollama 서비스 상태 확인"""
        try:
            import requests
            base_url = ollama_config.get('base_url', 'http://localhost:11434')
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama service not accessible: {str(e)}")
            return False
    
    def build_document(self, filepath: str) -> Any:
        """
        부모 클래스의 build_document 메서드를 오버라이드하여 
        각 processor 실행 시마다 콜백 호출
        """
        provider_cls = provider_from_filepath(filepath)
        layout_builder = self.resolve_dependencies(self.layout_builder_class)
        line_builder = self.resolve_dependencies(LayoutBuilder)
        ocr_builder = self.resolve_dependencies(OcrBuilder)
        provider = provider_cls(filepath, self.config)
        
        document = DocumentBuilder(self.config)(
            provider, layout_builder, line_builder, ocr_builder
        )
        
        structure_builder_cls = self.resolve_dependencies(StructureBuilder)
        structure_builder_cls(document)
        
        # 여기서부터가 콜백이 추가된 processor 실행 부분
        total_processors = len(self.processor_list)
        
        for i, processor in enumerate(self.processor_list):
            processor_name = processor.__class__.__name__
            
            # processor 실행 전 콜백
            self._notify_progress(
                processor_name, i, total_processors, 
                {"status": "starting", "message": f"Starting {processor_name}"}
            )
            
            try:
                # 실제 processor 실행
                start_time = time.time()
                processor(document)
                elapsed_time = time.time() - start_time
                
                # processor 실행 후 콜백
                self._notify_progress(
                    processor_name, i + 1, total_processors,
                    {
                        "status": "completed", 
                        "message": f"Completed {processor_name}",
                        "elapsed_time": elapsed_time
                    }
                )
                
            except Exception as e:
                # processor 실행 중 에러 발생 시 콜백
                self._notify_progress(
                    processor_name, i, total_processors,
                    {
                        "status": "error",
                        "message": f"Error in {processor_name}: {str(e)}",
                        "error": str(e)
                    }
                )
                # 에러를 다시 raise
                raise
        
        return document
    
    def _notify_progress(self, processor_name: str, current: int, total: int, extra_info: Dict[str, Any] = None):
        """진행상황 콜백 알림"""
        if self.progress_callback:
            self.progress_callback.notify(processor_name, current, total, extra_info)
    
    def __call__(self, pdf_path: str, **kwargs) -> Any:
        """
        PDF 파일을 처리 - 각 processor 실행 시마다 콜백이 호출됨
        
        Args:
            pdf_path: PDF 파일 경로
            **kwargs: 추가 처리 옵션
            
        Returns:
            변환된 결과 (Marker의 출력 형태)
        """
        # 부모 클래스의 __call__ 메서드 호출
        # 이 과정에서 build_document가 호출되고, 각 processor마다 콜백이 실행됨
        return super().__call__(pdf_path, **kwargs)
    
    def add_progress_callback(self, callback: Callable[[str, int, int, Dict[str, Any]], None]):
        """진행상황 콜백 함수 추가"""
        self.progress_callback.add_callback(callback)
    
    def remove_progress_callback(self, callback: Callable[[str, int, int, Dict[str, Any]], None]):
        """진행상황 콜백 함수 제거"""
        self.progress_callback.remove_callback(callback)
    
    def cleanup_resources(self):
        """리소스 정리"""
        try:
            gc.collect()
            self.logger.info("MarkerPDFConverter resources cleaned up")
        except Exception as e:
            self.logger.warning(f"Error cleaning up resources: {str(e)}")
    
    def __del__(self):
        """소멸자"""
        self.cleanup_resources()


