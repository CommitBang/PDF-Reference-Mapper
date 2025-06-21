@echo off
chcp 65001 >nul
:: Marker PDF Processor GPU 설치 스크립트 for Windows

echo 🚀 PDF Mapper - Marker 설치 시작...
echo.

:: 1. PyTorch GPU 버전 설치 (CUDA 12.8)
echo 📦 Step 1: PyTorch CUDA 12.8 설치 중...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if %errorlevel% neq 0 (
    echo ❌ PyTorch 설치 실패
    pause
    exit /b 1
)
echo ✅ PyTorch 설치 완료
echo.

:: 2. Marker 설치
echo 📦 Step 2: Marker 라이브러리 설치 중...
pip install marker-pdf[full]
if %errorlevel% neq 0 (
    echo ❌ Marker 설치 실패
    pause
    exit /b 1
)
echo ✅ Marker 설치 완료
echo.

:: 3. 나머지 dependencies 설치
echo 📦 Step 3: 나머지 dependencies 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Dependencies 설치 실패
    pause
    exit /b 1
)
echo ✅ Dependencies 설치 완료
echo.

:: 4. spaCy 모델 다운로드
echo 📦 Step 4: spaCy 모델 다운로드 중...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo ❌ spaCy 모델 다운로드 실패
    pause
    exit /b 1
)
echo ✅ spaCy 모델 다운로드 완료
echo.

:: 5. 설치 확인
echo 🧪 설치 확인 중...
python -c "import torch; print(f'✅ PyTorch version: {torch.__version__}'); print(f'✅ CUDA available: {torch.cuda.is_available()}'); torch.cuda.is_available() and print(f'✅ CUDA version: {torch.version.cuda}') and print(f'✅ GPU device: {torch.cuda.get_device_name(0)}'); import marker; print('✅ Marker library available'); print('✅ 모든 라이브러리 설치 완료')"

echo.
echo 🎉 Marker 설치 완료!
echo.
echo ✨ Marker의 장점:
echo    - Nougat보다 빠르고 정확한 PDF 변환
echo    - 최신 라이브러리로 호환성 문제 없음
echo    - 더 나은 레이아웃 이해 및 텍스트 구조화
echo    - 다양한 문서 형식 지원 (PDF, DOCX, PPTX 등)
echo.
echo 테스트를 실행하려면:
echo    python test_marker_setup.py
echo.
echo API 서버를 시작하려면:
echo    python -m app.main
echo.
pause