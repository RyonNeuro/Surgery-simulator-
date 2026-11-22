#!/usr/bin/env python3
"""Claude <-> ChatGPT 토론 스크립트.

GitHub 이슈의 제목/본문(+ 기존 댓글)을 주제로 삼아
Claude(제안) -> GPT(비평) -> Claude(반영) ... 순서로 몇 라운드 토론하고,
각 발언을 이슈 댓글로 남긴 뒤 마지막에 Claude가 합의안을 정리한다.

외부 패키지 없이 표준 라이브러리만 사용한다.
"""
import json
import os
import pathlib
import sys
import urllib.request
import urllib.error

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GH_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
ISSUE = os.environ["ISSUE_NUMBER"]

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL") or "claude-sonnet-5-5"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5"
ROUNDS = int(os.environ.get("DEBATE_ROUNDS") or "2")
MAX_FILE_CHARS = 40_000

ROOT = pathlib.Path(__file__).resolve().parent.parent


def http_json(url, payload=None, headers=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{url} -> HTTP {e.code}: {body[:500]}") from None


# ---------- GitHub ----------
GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}


def gh(path, payload=None, method=None):
    return http_json(f"https://api.github.com/repos/{REPO}{path}", payload, GH_HEADERS, method)


def post_comment(body):
    gh(f"/issues/{ISSUE}/comments", {"body": body}, method="POST")


# ---------- 모델 호출 ----------
def ask_claude(system, messages):
    if not ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY 시크릿이 없습니다.")
    res = http_json(
        "https://api.anthropic.com/v1/messages",
        {"model": CLAUDE_MODEL, "max_tokens": 16000, "system": system, "messages": messages},
        {
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    text = "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text")
    if not text.strip():
        kinds = [b.get("type") for b in res.get("content", [])]
        raise RuntimeError(f"Claude 응답이 비어 있음 (stop_reason={res.get('stop_reason')}, blocks={kinds})")
    return text


def ask_gpt(system, messages):
    if not OPENAI_KEY:
        raise RuntimeError("OPENAI_API_KEY 시크릿이 없습니다.")
    res = http_json(
        "https://api.openai.com/v1/chat/completions",
        {"model": OPENAI_MODEL, "messages": [{"role": "system", "content": system}] + messages},
        {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
    )
    return res["choices"][0]["message"]["content"]


# ---------- 컨텍스트 ----------
def project_context():
    parts = []
    for name in ["AGENTS.md", "index.html"]:
        p = ROOT / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
            parts.append(f"### {name}\n```\n{text}\n```")
    return "\n\n".join(parts)


def issue_context():
    issue = gh(f"/issues/{ISSUE}")
    comments = gh(f"/issues/{ISSUE}/comments?per_page=50") or []
    lines = [f"# 이슈: {issue['title']}", issue.get("body") or ""]
    for c in comments:
        body = (c.get("body") or "").strip()
        if "<!-- ai-debate -->" in body or body.startswith("/토론"):
            continue  # 이전 AI 발언·실행 명령은 제외(사용자 의견만)
        lines.append(f"\n[사용자 댓글] {c['body']}")
    return "\n".join(lines)


SYSTEM_COMMON = (
    "당신은 신경외과 동맥류 클립결찰 시뮬레이터(브라우저용 HTML/JS) 개발 토론에 참여합니다. "
    "사용자는 신경외과 의사이고 폰으로 작업합니다. 한국어로, 구체적으로, 짧게 말하세요. "
    "코드 변경을 제안할 땐 어떤 파일의 어느 부분을 어떻게 바꿀지 명확히 쓰세요."
)
CLAUDE_SYS = SYSTEM_COMMON + " 당신(Claude)은 제안자입니다. 비평을 받으면 타당한 건 받아들이고, 아닌 건 근거를 들어 반박하세요."
GPT_SYS = SYSTEM_COMMON + " 당신(ChatGPT)은 비평자입니다. 제안의 약점, 버그, 의학적 부정확성, 더 나은 대안을 날카롭게 지적하세요. 동의하는 부분은 짧게만."


def tag(who, round_no, text):
    return f"<!-- ai-debate -->\n### {who} · 라운드 {round_no}\n\n{text}"


def main():
    topic = issue_context()
    ctx = project_context()
    transcript = []  # (speaker, text)

    def as_messages(for_claude):
        intro = f"{topic}\n\n---\n현재 프로젝트 파일:\n{ctx}"
        msgs = [{"role": "user", "content": intro}]
        for speaker, text in transcript:
            mine = (speaker == "Claude") == for_claude
            msgs.append({"role": "assistant" if mine else "user", "content": f"[{speaker}] {text}"})
        if msgs[-1]["role"] == "assistant":
            msgs.append({"role": "user", "content": "계속하세요."})
        return msgs

    post_comment(f"<!-- ai-debate -->\n🤖 토론 시작 — Claude(`{CLAUDE_MODEL}`) vs ChatGPT(`{OPENAI_MODEL}`), {ROUNDS}라운드")

    for r in range(1, ROUNDS + 1):
        c = ask_claude(CLAUDE_SYS, as_messages(True))
        transcript.append(("Claude", c))
        post_comment(tag("🟠 Claude (제안)", r, c))

        g = ask_gpt(GPT_SYS, as_messages(False))
        transcript.append(("ChatGPT", g))
        post_comment(tag("🟢 ChatGPT (비평)", r, g))

    final_msgs = as_messages(True)
    final_msgs[-1]["content"] += (
        "\n\n토론을 마무리합니다. 최종 합의안을 정리하세요: "
        "1) 채택할 변경사항 체크리스트(- [ ] 형식), 2) 남은 이견, 3) 다음에 사용자가 결정할 것."
    )
    summary = ask_claude(CLAUDE_SYS, final_msgs)
    post_comment(f"<!-- ai-debate -->\n## ✅ 최종 합의안\n\n{summary}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 실패 사유를 이슈에 남겨 폰에서도 보이게
        try:
            post_comment(f"<!-- ai-debate -->\n⚠️ 토론 실행 실패: `{e}`")
        finally:
            sys.exit(1)
