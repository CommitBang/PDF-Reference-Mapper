import logging
import requests
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.util import classes_to_strings
from app.services.layout_rendere import LayoutRenderer

layout_renderer_path = classes_to_strings([LayoutRenderer])[0]

class MarkerInitializer:
    def __init__(self, model_config, ollama_config, logger=None):
        self.model_config = model_config
        self.ollama_config = ollama_config
        self.logger = logger or logging.getLogger(__name__)

    def check_ollama_service(self) -> bool:
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

    def initialize(self):
        self.logger.info("Loading Marker models...")
        model_dict = create_model_dict()
        marker_config = {"output_format": "json", 'disable_image_extraction': True}
        if self.ollama_config.get('enabled', False) and self.check_ollama_service():
            self.logger.info("Initializing Ollama LLM service...")
            marker_config.update({
                "use_llm": True,
                "llm_service": "marker.services.ollama.OllamaService",
                "ollama_base_url": self.ollama_config.get('base_url', 'http://localhost:11434'),
                "ollama_model": self.ollama_config.get('model', 'llama2')
            })
            self.logger.info(f"Ollama service configured with model: {self.ollama_config.get('model', 'llama2')}")
        else:
            self.logger.info("Ollama service not enabled or not accessible, proceeding without LLM support")
        config_parser = ConfigParser(marker_config)
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=model_dict,
            processor_list=config_parser.get_processors(),
            renderer=layout_renderer_path,
            llm_service=config_parser.get_llm_service()
        )
        self.logger.info("Marker models loaded successfully")
        return converter 