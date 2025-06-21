import logging
import requests
from app.config.settings import config


class OllamaService:
    """
    Service for generating references using Ollama.
    """
    
    def __init__(self, rule: str | None = None):
        self.logger = logging.getLogger(__name__)
        llm_config = config.get_llm_service_config()
        if not llm_config.get('enabled'):
            raise ValueError('Ollama is not enabled')
        self.model = llm_config.get('model')
        self.base_url = llm_config.get('base_url')
        self.rule = rule

    def _generate_prompt(self, prompt: str) -> str:
        if self.rule:
            return f'rule: {self.rule}\n\n{prompt}'

    def response(self, prompt: str) -> str:
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json = {
                    'model': self.model,
                    'prompt': self._generate_prompt(prompt),
                    'temperature': 0.2,
                    'max_tokens': 2048,
                    'timeout': 15,
                    'stream': False
                }
            )
            if response.status_code == 200:
                return response.json().get('response', {})
            else:
                self.logger.error(f'Error generating response: {response.status_code} {response.text}')
                return {}
        except Exception as e:
            self.logger.error(f'Error generating response: {e}')
            return {}