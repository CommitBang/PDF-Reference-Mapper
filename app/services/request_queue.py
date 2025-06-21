import asyncio
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """대기큐의 작업을 나타내는 클래스"""
    id: str
    created_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    result: Any = None
    error_message: str = ""
    processor_func: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    updated_at: Optional[datetime] = None

    def update_status(self, status: TaskStatus, progress: int = None, result: Any = None, error_message: str = ""):
        """작업 상태 업데이트"""
        self.status = status
        self.updated_at = datetime.now()
        if progress is not None:
            self.progress = progress
        if result is not None:
            self.result = result
        if error_message:
            self.error_message = error_message


class RequestQueue:
    """동시 요청을 순차적으로 처리하는 대기큐 시스템"""
    
    def __init__(self, max_concurrent_tasks: int = 1):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.pending_tasks: Dict[str, QueueTask] = {}
        self.processing_tasks: Dict[str, QueueTask] = {}
        self.completed_tasks: Dict[str, QueueTask] = {}
        self.failed_tasks: Dict[str, QueueTask] = {}
        
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._logger = logging.getLogger(__name__)
        
        # 워커 스레드 시작
        self._start_worker()
    
    def _start_worker(self):
        """워커 스레드 시작"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            self._logger.info("Request queue worker thread started")
    
    def _worker_loop(self):
        """워커 루프 - 대기 중인 작업을 처리"""
        while not self._stop_event.is_set():
            try:
                # 처리할 작업이 있는지 확인
                with self._lock:
                    if (len(self.processing_tasks) < self.max_concurrent_tasks and 
                        len(self.pending_tasks) > 0):
                        
                        # 가장 오래된 작업을 가져옴
                        task_id = min(self.pending_tasks.keys(), 
                                    key=lambda x: self.pending_tasks[x].created_at)
                        task = self.pending_tasks.pop(task_id)
                        
                        # 처리 중 상태로 변경
                        task.update_status(TaskStatus.PROCESSING)
                        self.processing_tasks[task_id] = task
                        
                        self._logger.info(f"Starting task {task_id}")
                
                # 락 외부에서 실제 작업 처리
                if 'task' in locals():
                    self._process_task(task)
                    del task
                
                # 짧은 대기
                time.sleep(0.1)
                
            except Exception as e:
                self._logger.error(f"Worker loop error: {str(e)}")
                time.sleep(1)
    
    def _process_task(self, task: QueueTask):
        """실제 작업 처리"""
        try:
            # 작업 실행
            if task.processor_func:
                result = task.processor_func(*task.args, **task.kwargs)
                
                with self._lock:
                    # 성공 상태로 업데이트
                    task.update_status(TaskStatus.COMPLETED, progress=100, result=result)
                    
                    # 처리 중에서 완료로 이동
                    if task.id in self.processing_tasks:
                        del self.processing_tasks[task.id]
                    self.completed_tasks[task.id] = task
                    
                self._logger.info(f"Task {task.id} completed successfully")
            else:
                raise ValueError("No processor function provided")
                
        except Exception as e:
            with self._lock:
                # 실패 상태로 업데이트
                task.update_status(TaskStatus.FAILED, error_message=str(e))
                
                # 처리 중에서 실패로 이동
                if task.id in self.processing_tasks:
                    del self.processing_tasks[task.id]
                self.failed_tasks[task.id] = task
                
            self._logger.error(f"Task {task.id} failed: {str(e)}")
    
    def submit_task(self, processor_func: Callable, *args, **kwargs) -> str:
        """새 작업을 큐에 추가"""
        task_id = str(uuid.uuid4())
        task = QueueTask(
            id=task_id,
            created_at=datetime.now(),
            processor_func=processor_func,
            args=args,
            kwargs=kwargs
        )
        
        with self._lock:
            self.pending_tasks[task_id] = task
        
        self._logger.info(f"Task {task_id} submitted to queue")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """작업 상태 조회"""
        with self._lock:
            # 모든 상태에서 작업 검색
            for task_dict in [self.pending_tasks, self.processing_tasks, 
                            self.completed_tasks, self.failed_tasks]:
                if task_id in task_dict:
                    return task_dict[task_id]
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소 (대기 중인 작업만 가능)"""
        with self._lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks.pop(task_id)
                task.update_status(TaskStatus.CANCELLED)
                # 취소된 작업도 완료된 작업으로 처리 (상태 추적용)
                self.completed_tasks[task_id] = task
                self._logger.info(f"Task {task_id} cancelled")
                return True
        return False
    
    def get_queue_status(self) -> Dict[str, int]:
        """큐 전체 상태 조회"""
        with self._lock:
            return {
                "pending": len(self.pending_tasks),
                "processing": len(self.processing_tasks),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks)
            }
    
    def get_queue_position(self, task_id: str) -> Optional[int]:
        """작업의 큐 내 위치 조회 (1부터 시작)"""
        with self._lock:
            if task_id in self.pending_tasks:
                sorted_tasks = sorted(self.pending_tasks.items(), 
                                    key=lambda x: x[1].created_at)
                for i, (tid, _) in enumerate(sorted_tasks):
                    if tid == task_id:
                        return i + 1
        return None
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """완료된 작업 정리 (메모리 관리)"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self._lock:
            # 완료된 작업 정리
            to_remove = []
            for task_id, task in self.completed_tasks.items():
                if task.updated_at and task.updated_at.timestamp() < cutoff_time:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.completed_tasks[task_id]
            
            # 실패한 작업 정리
            to_remove = []
            for task_id, task in self.failed_tasks.items():
                if task.updated_at and task.updated_at.timestamp() < cutoff_time:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.failed_tasks[task_id]
        
        if to_remove:
            self._logger.info(f"Cleaned up {len(to_remove)} old tasks")
    
    def stop(self):
        """큐 시스템 종료"""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        self._logger.info("Request queue stopped")
    
    def __del__(self):
        """소멸자"""
        self.stop()


# 전역 큐 인스턴스 (싱글톤 패턴)
_global_queue = None

def get_request_queue() -> RequestQueue:
    """전역 요청 큐 가져오기"""
    global _global_queue
    if _global_queue is None:
        _global_queue = RequestQueue(max_concurrent_tasks=1)  # 순차 처리
    return _global_queue