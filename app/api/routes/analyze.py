from flask import Blueprint, request, Response
from app.services.marker_ocr_service import MarkerOCRService
from app.services.marker_pdf_converter import ProgressCallback
from app.services.reference_mapper import ReferenceMapper
from app.services.request_queue import get_request_queue, TaskStatus
from app.utils.gpu_utils import gpu_manager
from app.api.models import StreamResponse, Metadata, AnalysisResponse
import tempfile
import os
import time
import json
import logging
from queue import Queue
from threading import Thread

analyze_blueprint = Blueprint('analyze', __name__)
reference_mapper = ReferenceMapper()
request_queue = get_request_queue()
logger = logging.getLogger(__name__)

def create_stream_response(status, message, data=None, progress=None):
    response = StreamResponse(status=status, message=message, data=data, progress=progress)
    return f"data: {json.dumps(response.to_dict())}\n\n"

def process_pdf_task(file_content, filename, args, headers, progress_queue=None):
    """PDF 처리 작업 함수 (큐에서 실행됨)"""
    start_time = time.time()
    temp_file_path = None
    
    def send_progress(status, message, progress=None):
        """진행상황을 큐로 전송"""
        if progress_queue:
            try:
                progress_queue.put({
                    'status': status,
                    'message': message,
                    'progress': progress,
                    'timestamp': time.time()
                }, timeout=1)
            except Exception:
                pass  # 큐가 가득 찬 경우 무시
    
    try:
        if filename == '':
            raise ValueError('No file selected')
        if not filename.lower().endswith('.pdf'):
            raise ValueError('Only PDF files are supported')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        send_progress('progress', 'GPU Memory allocation checking', 25)
        memory_info = gpu_manager.check_gpu_memory()
        if not gpu_manager.allocate_model_memory('marker'):
            logger.warning('Could not allocate optimal GPU memory for Marker')
        
        send_progress('progress', 'GPU Memory allocated', 30)
        
        # 진행상황 콜백을 위한 큐와 콜백 함수 설정
        def processor_progress_callback(processor_name, current, total, extra_info):
            """각 processor 실행 시 호출되는 콜백"""
            status = extra_info.get('status', 'unknown')
            if status == 'starting':
                progress = 30 + int((current / total) * 50)  # 30-80% 범위
                send_progress('progress', f'Starting {processor_name} ({current+1}/{total})', progress)
            elif status == 'completed':
                progress = 30 + int(((current) / total) * 50)  # 30-80% 범위
                elapsed = extra_info.get('elapsed_time', 0)
                send_progress('progress', f'Completed {processor_name} ({elapsed:.2f}s)', progress)
        
        # 진행상황 콜백 설정
        progress_callback = ProgressCallback()
        progress_callback.add_callback(processor_progress_callback)
        
        # MarkerOCRService 인스턴스 생성 (콜백 포함)
        ocr_service = MarkerOCRService(progress_callback=progress_callback)
        
        try:
            send_progress('progress', 'Starting Marker PDF processing', 30)
            result = ocr_service.process_pdf(temp_file_path)
            send_progress('progress', 'Marker processing completed', 80)
            
            ocr_service.cleanup_resources()
            send_progress('progress', 'Resources cleaned up', 85)
            
            send_progress('progress', 'Mapping references', 90)
            result.pages = reference_mapper.map_references(result.pages, result.figures)
            send_progress('progress', 'References mapped', 95)
            
        except Exception as e:
            logger.error(f"Marker processing failed: {str(e)}")
            gpu_manager.handle_oom_error('marker')
            raise
        
        processing_time = time.time() - start_time
        file_size = os.path.getsize(temp_file_path)
        metadata = Metadata(
            filename=filename,
            total_pages=len(result.pages),
            file_size=file_size,
            processing_time=processing_time,
            processor='marker'
        )
        response = AnalysisResponse(metadata=metadata, pages=result.pages, figures=result.figures)
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file: {str(e)}")


@analyze_blueprint.route('/analyze', methods=['POST'])
def analyze():
    headers = dict(request.headers)
    files = request.files
    args = request.args

    logger.info(f"POST /analyze called - Headers: {headers}")
    logger.info(f"POST /analyze called - Files: {list(files.keys())}")
    logger.info(f"POST /analyze called - Args: {dict(args)}")

    if 'file' not in files:
        def error_gen():
            yield create_stream_response('error', 'No file provided')
        return Response(error_gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Access-Control-Allow-Origin': '*', 'X-Accel-Buffering': 'no'})

    file = files['file']
    filename = file.filename
    file_content = file.read()

    # 진행상황 전송을 위한 큐 생성
    progress_queue = Queue(maxsize=100)
    
    # 작업을 큐에 제출 (진행상황 큐 포함)
    task_id = request_queue.submit_task(process_pdf_task, file_content, filename, args, headers, progress_queue)
    
    def generate_with_queue():
        """큐를 통한 스트리밍 응답 생성 - 실시간 진행상황 포함"""
        # 처음에는 기존과 동일하게 시작
        yield create_stream_response('started', 'Analysis started')
        
        # 파일 검증은 즉시 수행
        if filename == '':
            yield create_stream_response('error', 'No file selected')
            return
        if not filename.lower().endswith('.pdf'):
            yield create_stream_response('error', 'Only PDF files are supported')
            return
        
        yield create_stream_response('progress', 'File validation completed', progress=10)
        
        # 큐 대기 중일 때는 기존 메시지 형태로 표시
        position = request_queue.get_queue_position(task_id)
        if position and position > 1:
            yield create_stream_response('progress', f'Waiting for available resources... (Queue position: {position})', progress=15)
        
        # 작업 상태 모니터링
        has_started_processing = False
        while True:
            task = request_queue.get_task_status(task_id)
            if not task:
                yield create_stream_response('error', 'Task not found')
                break
            
            if task.status == TaskStatus.PENDING:
                position = request_queue.get_queue_position(task_id)
                if position and position > 1:
                    yield create_stream_response('progress', f'Waiting for available resources... (Position in queue: {position})', progress=15)
                else:
                    yield create_stream_response('progress', 'Preparing for processing...', progress=18)
                time.sleep(1)
                continue
            
            elif task.status == TaskStatus.PROCESSING:
                if not has_started_processing:
                    yield create_stream_response('progress', f'Processing PDF: {filename}', progress=20)
                    has_started_processing = True
                
                # 실시간 진행상황을 progress_queue에서 읽어서 전송
                while task.status == TaskStatus.PROCESSING:
                    # progress_queue에서 진행상황 읽기
                    try:
                        progress_info = progress_queue.get(timeout=0.5)
                        yield create_stream_response(
                            progress_info['status'],
                            progress_info['message'],
                            progress=progress_info.get('progress')
                        )
                    except:
                        # 큐가 비어있거나 타임아웃 발생
                        pass
                    
                    # 작업 상태 업데이트
                    task = request_queue.get_task_status(task_id)
                    if not task:
                        break
                continue
            
            elif task.status == TaskStatus.COMPLETED:
                # 남은 진행상황 메시지들 처리
                while not progress_queue.empty():
                    try:
                        progress_info = progress_queue.get_nowait()
                        yield create_stream_response(
                            progress_info['status'],
                            progress_info['message'],
                            progress=progress_info.get('progress')
                        )
                    except:
                        break
                
                # 완료 메시지
                if task.result and 'metadata' in task.result:
                    processing_time = task.result['metadata']['processing_time']
                    yield create_stream_response('completed', f'Analysis completed in {processing_time:.2f} seconds', data=task.result, progress=100)
                else:
                    yield create_stream_response('completed', 'Analysis completed', data=task.result, progress=100)
                break
            
            elif task.status == TaskStatus.FAILED:
                if 'Marker processing failed' in task.error_message:
                    yield create_stream_response('error', f'Marker processing failed: {task.error_message}')
                else:
                    yield create_stream_response('error', f'Internal server error: {task.error_message}')
                break
            
            elif task.status == TaskStatus.CANCELLED:
                yield create_stream_response('error', 'Processing was cancelled')
                break
            
            time.sleep(0.1)  # 더 빠른 응답을 위해 간격 단축
    
    return Response(generate_with_queue(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Access-Control-Allow-Origin': '*', 'X-Accel-Buffering': 'no'})


@analyze_blueprint.route('/queue/status', methods=['GET'])
def get_queue_status():
    """큐 전체 상태 조회"""
    status = request_queue.get_queue_status()
    return {
        'queue_status': status,
        'timestamp': time.time()
    }


@analyze_blueprint.route('/queue/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """특정 작업 상태 조회"""
    task = request_queue.get_task_status(task_id)
    if not task:
        return {'error': 'Task not found'}, 404
    
    return {
        'task_id': task.id,
        'status': task.status.value,
        'progress': task.progress,
        'created_at': task.created_at.isoformat(),
        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
        'queue_position': request_queue.get_queue_position(task_id),
        'error_message': task.error_message if task.error_message else None
    }


@analyze_blueprint.route('/queue/task/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """작업 취소"""
    success = request_queue.cancel_task(task_id)
    if success:
        return {'message': f'Task {task_id} cancelled successfully'}
    else:
        return {'error': 'Task not found or cannot be cancelled'}, 400 