# 프로젝트 안내 (Claude · ChatGPT 공통)

## 무엇을 만드나
- 뇌동맥류 클립결찰(aneurysm clipping) 연습용 **브라우저 시뮬레이터**
- 사용자: 신경외과 의사. 저사양 노트북 → **폰 브라우저에서 돌아가야 함**

## 기술 원칙
- 빌드 도구 없이 `index.html` 하나(HTML + CSS + JS)로 시작. 외부 라이브러리는 CDN만.
- 터치 조작 우선(손가락 드래그), 화면 세로 모드 기준.
- GitHub Pages로 배포 → `https://ryonneuro.github.io/surgery-simulator-/`

## 작업 방식
- 기능 아이디어나 문제는 **이슈**로 올림 → 제목이 `[토론]`으로 시작하면 Claude와 ChatGPT가 자동 토론(`.github/workflows/debate.yml`).
- 토론 최종 합의안의 체크리스트를 Claude Code가 실제 코드로 반영.
- 의학적 내용(해부, 클립 위치, 합병증)은 근거와 함께 쓰고, 불확실하면 그렇다고 밝힐 것.
