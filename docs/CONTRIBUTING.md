# 기여 가이드라인 (CONTRIBUTING)

감사합니다! PDF 인식 API 프로젝트에 기여하고자 한다면 아래 가이드라인을 따라주세요.

## 개발 환경 세팅

```bash
cd pdfrec
pip install -r requirements.txt
```
혹은
```
python setup.py
```

## 코드 스타일
- [black](https://github.com/psf/black) 코드 포맷터 사용
- [flake8](https://flake8.pycqa.org/) 린터 사용
- 함수/클래스/변수명은 명확하고 일관성 있게 작성
- 주석 및 docstring 적극 활용

## 커밋 메시지 규칙
- 명확하고 간결하게 작성
- 예시: `fix: PDF 업로드 오류 수정`, `feat: 표 자동 감지 기능 추가`

## Pull Request(PR) 작성법
- 기능/버그별 브랜치 생성 후 PR 제출
- PR 설명에 변경사항, 테스트 방법, 관련 이슈 명시
- 리뷰어의 피드백 반영 후 머지

## 이슈 작성법
- 버그/기능/문서/질문 등 유형 명시
- 재현 방법, 기대 결과, 실제 결과 상세 기재

## 테스트
- 주요 기능 추가/수정 시 테스트 코드 작성 권장
- `pytest`로 테스트 실행

## 코드 리뷰
- 모든 PR은 최소 1명 이상의 리뷰 필요
- 리뷰어는 코드 품질, 문서화, 테스트 여부 확인

## 기타
- 자세한 사항은 README 및 각종 문서 참고 