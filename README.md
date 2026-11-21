# 동맥류 클립결찰 시뮬레이터

폰 브라우저에서 돌아가는 뇌동맥류 클립결찰 연습 시뮬레이터.
Claude와 ChatGPT가 GitHub 이슈에서 토론하며 발전시킵니다.

▶ **실행**: https://ryonneuro.github.io/surgery-simulator-/

## AI 토론 쓰는 법 (폰에서)
1. 이 repo의 **Issues → New issue**
2. 제목을 `[토론] ...` 으로 시작 (예: `[토론] 클립 각도 조작을 두 손가락 회전으로 바꾸기`)
3. 본문에 원하는 것/문제점을 자유롭게 적고 등록
4. 1~3분 뒤 이슈 댓글에 Claude(제안) ↔ ChatGPT(비평) 토론과 **최종 합의안**이 달림
5. 기존 이슈에서 다시 돌리려면 댓글로 `/토론`

합의안이 마음에 들면 Claude Code에게 "이슈 #N 합의안 반영해줘"라고 하면 됩니다.

## 처음 한 번만 설정
- **Settings → Secrets and variables → Actions → New repository secret**
  - `ANTHROPIC_API_KEY` (console.anthropic.com)
  - `OPENAI_API_KEY` (platform.openai.com)
- (선택) 같은 화면의 **Variables** 탭
  - `CLAUDE_MODEL` 기본 `claude-sonnet-5-5`
  - `OPENAI_MODEL` 기본 `gpt-5`
  - `DEBATE_ROUNDS` 기본 `2`
- **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**

## 구조
```
index.html                  시뮬레이터 (HTML+JS 한 파일)
AGENTS.md / CLAUDE.md       두 AI가 공통으로 읽는 프로젝트 안내
scripts/debate.py           토론 스크립트
.github/workflows/debate.yml 이슈 → 토론 자동 실행
```
