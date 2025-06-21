# 브랜치 전략

이 프로젝트는 Git-flow에 기반한 브랜치 전략을 사용합니다. 각 브랜치의 역할은 다음과 같으며, 기여 시 이 규칙을 따라주시기 바랍니다.

## 🌳 주요 브랜치

-   **`main`**:
    -   배포 가능한 프로덕션 코드를 위한 브랜치입니다.
    -   오직 `develop` 브랜치와 `hotfix` 브랜치로부터 병합(Merge)됩니다.
    -   직접적인 커밋은 허용되지 않습니다.

-   **`develop`**:
    -   다음 릴리즈를 위해 개발 중인 최신 코드를 포함하는 브랜치입니다.
    -   모든 `feature` 브랜치가 병합되는 중심 브랜치입니다.
    -   `main` 브랜치로 병합하여 새로운 버전을 릴리즈합니다.

## 🌿 보조 브랜치

-   **`feature/{feature-name}`**:
    -   새로운 기능을 개발하기 위한 브랜치입니다.
    -   `develop` 브랜치에서 분기합니다.
    -   기능 개발이 완료되면 `develop` 브랜치로 Pull Request를 생성하여 병합합니다.
    -   예시: `feature/user-authentication`, `feature/pdf-analysis-sse`

-   **`fix/{issue-number}-{short-description}`**:
    -   `develop` 브랜치에서 발생한 버그를 수정하기 위한 브랜치입니다.
    -   `develop` 브랜치에서 분기합니다.
    -   수정이 완료되면 `develop` 브랜치로 Pull Request를 생성하여 병합합니다.
    -   예시: `fix/123-file-upload-error`

-   **`hotfix/{version}`**:
    -   배포된 `main` 브랜치에서 발생한 긴급한 버그를 수정하기 위한 브랜치입니다.
    -   `main` 브랜치에서 분기합니다.
    -   수정이 완료되면 `main`과 `develop` 브랜치 모두에 병합하여 수정 사항을 동기화합니다.
    -   예시: `hotfix/1.0.1`

## 🚀 워크플로우 예시

### 새로운 기능 개발

1.  `develop` 브랜치에서 최신 코드를 가져옵니다.
    ```bash
    git checkout develop
    git pull origin develop
    ```
2.  새로운 기능 브랜치를 생성합니다.
    ```bash
    git checkout -b feature/awesome-new-feature
    ```
3.  기능을 개발하고 커밋합니다.
4.  개발이 완료되면 `develop` 브랜치로 Pull Request를 보냅니다.

### 버그 수정

1.  `develop` 브랜치에서 최신 코드를 가져옵니다.
2.  버그 수정을 위한 브랜치를 생성합니다.
    ```bash
    git checkout -b fix/45-fix-minor-bug
    ```
3.  버그를 수정하고 커밋합니다.
4.  수정이 완료되면 `develop` 브랜치로 Pull Request를 보냅니다. 