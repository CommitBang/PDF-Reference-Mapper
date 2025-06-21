import yaml
import os
from typing import Dict, Any


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_data = {}
        self.load_config(config_path)
    
    def load_config(self, path: str) -> None:
        """Load configuration from YAML file"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as file:
                self.config_data = yaml.safe_load(file)
        else:
            raise FileNotFoundError(f"Configuration file not found: {path}")
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Return model-specific configuration"""
        return self.config_data.get('models', {}).get(model_name, {})
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """Return hardware configuration"""
        return self.config_data.get('hardware', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Return API configuration"""
        return self.config_data.get('api', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Return processing configuration"""
        return self.config_data.get('processing', {})
    
    def get_llm_service_config(self, service_name: str = 'ollama') -> Dict[str, Any]:
        """Return LLM service configuration"""
        return self.config_data.get('llm_services', {}).get(service_name, {})
    
    def get_reference_mapper_config(self) -> Dict[str, Any]:
        """Return reference mapper configuration"""
        return self.config_data.get('reference_mapper', {})
    
    def validate_hardware(self) -> bool:
        """Hardware compatibility verification"""
        hardware = self.get_hardware_config()
        gpu_memory = hardware.get('total_gpu_memory', 0)
        cpu_cores = hardware.get('cpu_cores', 1)
        
        # Basic validation
        if gpu_memory < 10:
            print(f"Warning: GPU memory ({gpu_memory}GB) may be insufficient for optimal performance")
        
        if cpu_cores < 4:
            print(f"Warning: CPU cores ({cpu_cores}) may be insufficient for optimal performance")
        
        return True


# Global config instance
config = Config()