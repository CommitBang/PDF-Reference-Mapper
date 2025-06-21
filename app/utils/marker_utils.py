import re
from bs4 import BeautifulSoup


def extract_text_from_html(html: str) -> str:
    """
    HTML에서 텍스트를 추출하며, 주요 태그의 줄바꿈을 유지합니다.

    - <br> 태그를 줄바꿈 문자로 변환합니다.
    - <p>, <div>와 같은 블록 레벨 요소 뒤에 줄바꿈을 추가하여 가독성을 높입니다.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, 'html.parser')

    # <br> 태그를 개행 문자로 교체
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # 블록 레벨 태그 뒤에 개행 문자 추가
    block_tags = ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre', 'tr', 'th', 'td']
    for tag in soup.find_all(block_tags):
        tag.append("\n")

    # BeautifulSoup을 이용해 텍스트 추출
    text = soup.get_text()

    # 여러 개의 개행 문자를 2개로 줄이고, 양쪽 공백 제거
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()

    return text 