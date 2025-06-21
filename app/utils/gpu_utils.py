import torch
import psutil
import logging
from typing import Dict, Optional, Generator
import gc
import time

from app.config.settings import config


# Memory allocation plan for modern architecture
MEMORY_ALLOCATION = {
    "marker": 5,   # GB
    "yolov8": 3,   # GB  
    "bert": 4,     # GB
    "sentence_transformer": 2,  # GB
    "buffer": 10   # GB (increased due to lower total usage)
}


class GPUMemoryManager:
    """
    GPU memory management utilities for RTX 3090 24GB optimization.
    Handles OOM prevention, model loading/unloading, and performance monitoring.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hardware_config = config.get_hardware_config()
        self.total_gpu_memory = self.hardware_config.get('total_gpu_memory', 24)
        self.allocated_models = {}
        
    def check_gpu_memory(self) -> Dict[str, float]:
        """
        Check current GPU memory status
        
        Returns:
            Dictionary with memory information in GB
        """
        try:
            if not torch.cuda.is_available():
                return {
                    'available': False,
                    'total': 0,
                    'allocated': 0,
                    'reserved': 0,
                    'free': 0
                }
            
            # Get memory info in bytes
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            total = torch.cuda.get_device_properties(0).total_memory
            
            # Convert to GB
            allocated_gb = allocated / (1024**3)
            reserved_gb = reserved / (1024**3)
            total_gb = total / (1024**3)
            free_gb = total_gb - allocated_gb
            
            memory_info = {
                'available': True,
                'total': round(total_gb, 2),
                'allocated': round(allocated_gb, 2),
                'reserved': round(reserved_gb, 2),
                'free': round(free_gb, 2),
                'utilization': round((allocated_gb / total_gb) * 100, 1)
            }
            
            return memory_info
            
        except Exception as e:
            self.logger.error(f"Error checking GPU memory: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def allocate_model_memory(self, model_name: str, size_gb: Optional[int] = None) -> bool:
        """
        Check if model can be allocated and reserve memory
        
        Args:
            model_name: Name of the model to allocate
            size_gb: Memory size in GB, uses default if None
            
        Returns:
            True if allocation successful, False otherwise
        """
        try:
            if size_gb is None:
                size_gb = MEMORY_ALLOCATION.get(model_name, 2)
            
            memory_info = self.check_gpu_memory()
            
            if not memory_info.get('available', False):
                self.logger.warning("GPU not available for memory allocation")
                return False
            
            free_memory = memory_info['free']
            
            if free_memory < size_gb:
                self.logger.warning(f"Insufficient GPU memory. Need {size_gb}GB, have {free_memory}GB")
                
                # Try to free memory from other models
                if self._try_free_memory(size_gb):
                    # Recheck after cleanup
                    memory_info = self.check_gpu_memory()
                    free_memory = memory_info['free']
                    
                    if free_memory < size_gb:
                        return False
                else:
                    return False
            
            # Record allocation
            self.allocated_models[model_name] = {
                'size_gb': size_gb,
                'allocated_at': time.time()
            }
            
            self.logger.info(f"Allocated {size_gb}GB for {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error allocating memory for {model_name}: {str(e)}")
            return False
    
    def _try_free_memory(self, needed_gb: float) -> bool:
        """Try to free memory by unloading less critical models"""
        try:
            # Priority for keeping models (lower number = higher priority)
            model_priority = {
                'marker': 1,    # Highest priority
                'bert': 2,
                'yolov8': 3,
                'sentence_transformer': 4  # Lowest priority
            }
            
            # Sort allocated models by priority (lowest priority first)
            sorted_models = sorted(
                self.allocated_models.items(),
                key=lambda x: model_priority.get(x[0], 99),
                reverse=True
            )
            
            freed_memory = 0
            for model_name, info in sorted_models:
                if freed_memory >= needed_gb:
                    break
                
                self.logger.info(f"Freeing memory from {model_name} ({info['size_gb']}GB)")
                self.cleanup_gpu_cache()
                
                freed_memory += info['size_gb']
                del self.allocated_models[model_name]
            
            return freed_memory >= needed_gb
            
        except Exception as e:
            self.logger.error(f"Error trying to free memory: {str(e)}")
            return False
    
    def cleanup_gpu_cache(self) -> None:
        """Clean up GPU cache and force garbage collection"""
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            # Force Python garbage collection
            gc.collect()
            
            self.logger.debug("GPU cache cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error cleaning GPU cache: {str(e)}")
    
    def monitor_memory_usage(self, interval: float = 1.0) -> Generator[Dict[str, float], None, None]:
        """
        Monitor GPU memory usage over time
        
        Args:
            interval: Monitoring interval in seconds
            
        Yields:
            Memory information dictionary
        """
        while True:
            try:
                memory_info = self.check_gpu_memory()
                yield memory_info
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring memory: {str(e)}")
                break
    
    def handle_oom_error(self, model_name: str = None, reduce_batch_size: bool = True) -> Dict[str, any]:
        """
        Handle Out of Memory errors with recovery strategies
        
        Args:
            model_name: Name of the model that caused OOM
            reduce_batch_size: Whether to suggest batch size reduction
            
        Returns:
            Dictionary with recovery suggestions
        """
        try:
            self.logger.error(f"OOM error encountered for model: {model_name}")
            
            # Clean up immediately
            self.cleanup_gpu_cache()
            
            memory_info = self.check_gpu_memory()
            
            recovery_suggestions = {
                'success': False,
                'cleanup_performed': True,
                'available_memory': memory_info.get('free', 0),
                'suggestions': []
            }
            
            # Suggest batch size reduction
            if reduce_batch_size:
                recovery_suggestions['suggestions'].append('Reduce batch size by half')
            
            # Suggest model unloading
            if self.allocated_models:
                recovery_suggestions['suggestions'].append('Unload unused models')
            
            # Suggest sequential processing
            recovery_suggestions['suggestions'].append('Use sequential processing instead of parallel')
            
            # Check if we have enough memory now
            if model_name and memory_info.get('free', 0) >= MEMORY_ALLOCATION.get(model_name, 2):
                recovery_suggestions['success'] = True
                recovery_suggestions['suggestions'].append('Retry with current memory state')
            
            return recovery_suggestions
            
        except Exception as e:
            self.logger.error(f"Error handling OOM: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_optimal_batch_size(self, model_name: str, base_batch_size: int = 4) -> int:
        """
        Calculate optimal batch size based on available memory
        
        Args:
            model_name: Name of the model
            base_batch_size: Base batch size to start with
            
        Returns:
            Recommended batch size
        """
        try:
            memory_info = self.check_gpu_memory()
            
            if not memory_info.get('available', False):
                return 1  # Minimum batch size for CPU
            
            free_memory = memory_info['free']
            model_memory = MEMORY_ALLOCATION.get(model_name, 2)
            
            # Estimate memory per batch item (rough approximation)
            memory_per_batch = model_memory / 4  # Assume base batch size of 4
            
            # Calculate how many batch items we can fit
            max_batch_items = int(free_memory / memory_per_batch)
            
            # Apply conservative factor
            recommended_batch = min(max_batch_items * 0.8, base_batch_size)
            
            return max(1, int(recommended_batch))
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal batch size: {str(e)}")
            return 1
    
    def get_system_info(self) -> Dict[str, any]:
        """Get comprehensive system information"""
        try:
            info = {
                'gpu': self.check_gpu_memory(),
                'cpu': {
                    'cores': psutil.cpu_count(),
                    'usage': psutil.cpu_percent(interval=1),
                    'available_cores': psutil.cpu_count(logical=False)
                },
                'ram': {
                    'total': round(psutil.virtual_memory().total / (1024**3), 2),
                    'available': round(psutil.virtual_memory().available / (1024**3), 2),
                    'used': round(psutil.virtual_memory().used / (1024**3), 2),
                    'percentage': psutil.virtual_memory().percent
                }
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {'error': str(e)}


# Global instance
gpu_manager = GPUMemoryManager()