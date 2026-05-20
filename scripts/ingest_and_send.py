"""
AI & Data Daily Report — 자동 INGEST + 이메일 발송 스크립트

사전 준비:
  1. Gmail 앱 비밀번호 발급
     Google 계정 → 보안 → 2단계 인증 ON → 앱 비밀번호 → 16자리 발급
  2. 비밀번호 등록 (Windows 자격 증명 관리자에 암호화 저장)
     python scripts/setup_credential.py
"""

import subprocess, smtplib, os, sys, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

try:
    import keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

# ── 경로 설정 ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR    = BASE_DIR / "scripts" / "logs"

# ── 이메일 설정 ────────────────────────────────────────────
TO_EMAIL   = "parkharm@gmail.com"
FROM_EMAIL = "parkharm@gmail.com"
KR_SERVICE = "AIData_DailyReport"   # Windows 자격 증명 관리자 서비스명

# ── 로깅 ──────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"{datetime.now():%Y-%m}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def get_password() -> str:
    """
    비밀번호 조회 순서:
      1순위 — Windows 자격 증명 관리자 (keyring, 암호화)
      2순위 — 환경변수 GMAIL_APP_PASSWORD (비권장)
    """
    # 1순위: keyring (Windows Credential Manager)
    if _KEYRING_AVAILABLE:
        pwd = keyring.get_password(KR_SERVICE, FROM_EMAIL)
        if pwd:
            log.info("자격 증명: Windows 자격 증명 관리자에서 로드")
            return pwd.replace(" ", "")

    # 2순위: 환경변수 (폴백, 경고 출력)
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if pwd:
        log.warning("자격 증명: 환경변수 사용 중 — setup_credential.py 실행을 권장합니다")
        return pwd

    return ""


def run_ingest(today: str) -> bool:
    """Claude Code CLI로 INGEST 실행."""
    log.info(f"INGEST 시작: {today}")
    claude_cmd = "claude.exe" if sys.platform == "win32" else "claude"
    result = subprocess.run(
        [claude_cmd, "--dangerously-skip-permissions", "-p", "오늘 리포트 만들어줘"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        timeout=1800,      # 30분 타임아웃
        encoding="utf-8",
    )
    if result.returncode != 0:
        log.error(f"INGEST 실패 (code {result.returncode})\n{result.stderr}")
        return False
    log.info("INGEST 완료")
    return True


def build_email_body(today: str, md_path: Path) -> str:
    """
    Gmail에서 깨지지 않는 이메일 본문 HTML 생성.
    inline style만 사용, CSS 변수·grid·flexbox 없음.
    마크다운 보고서에서 뉴스 제목·인사이트·트렌드를 파싱해 구성.
    """
    # 마크다운에서 뉴스 제목·URL·인사이트 간단 파싱
    news_rows = ""
    trends_rows = ""
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        import re

        # 뉴스 항목: "### 뉴스 N. 제목" 줄 추출
        news_items = re.findall(
            r"### 뉴스\s+\d+\.\s+(.+?)\n.*?\*\*출처\*\*.*?\[(.+?)\]\((.+?)\).*?\n.*?\*\*인사이트\*\*:\s+(.+?)(?:\n|$)",
            text, re.DOTALL
        )
        for title, outlet, url, insight in news_items[:10]:
            title   = title.strip()
            insight = insight.strip()[:120] + ("…" if len(insight.strip()) > 120 else "")
            news_rows += f"""
            <tr>
              <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;vertical-align:top">
                <a href="{url}" style="font-size:14px;font-weight:600;color:#1e40af;text-decoration:none">{title}</a>
                <div style="font-size:12px;color:#718096;margin-top:2px">{outlet}</div>
                <div style="font-size:13px;color:#92400e;background:#fffbeb;border-left:3px solid #f59e0b;padding:6px 10px;margin-top:6px;border-radius:0 4px 4px 0">{insight}</div>
              </td>
            </tr>"""

        # 트렌드 항목: "### 트렌드 N. 제목" 줄 추출
        trend_items = re.findall(r"### 트렌드\s+\d+\.\s+(.+?)\n(.*?)(?=###|\Z)", text, re.DOTALL)
        for tname, tbody in trend_items[:6]:
            desc = re.sub(r"\*\*.*?\*\*:?\s*", "", tbody.split("\n")[0]).strip()[:100]
            trends_rows += f"""
            <tr>
              <td style="padding:8px 14px;border-bottom:1px solid #e2e8f0">
                <span style="font-size:13px;font-weight:600;color:#5b21b6">▸ {tname.strip()}</span>
                <span style="font-size:12px;color:#718096;margin-left:8px">{desc}</span>
              </td>
            </tr>"""

    if not news_rows:
        news_rows = '<tr><td style="padding:10px 14px;color:#718096">첨부 파일을 열어 전체 리포트를 확인하세요.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:24px 0">
  <tr><td align="center">
    <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">

      <!-- 헤더 -->
      <tr>
        <td style="background:linear-gradient(135deg,#1e3a5f,#1e40af);padding:24px 28px">
          <div style="font-size:12px;color:rgba(255,255,255,.7);margin-bottom:4px">{today}</div>
          <div style="font-size:22px;font-weight:700;color:#ffffff">AI &amp; Data Daily Report</div>
          <div style="font-size:12px;color:rgba(255,255,255,.65);margin-top:4px">큐레이터: Claude AI</div>
        </td>
      </tr>

      <!-- 안내 -->
      <tr>
        <td style="background:#eff6ff;padding:10px 28px;border-bottom:1px solid #bfdbfe">
          <span style="font-size:13px;color:#1e40af">📎 전체 리포트는 <strong>첨부 파일(AIData_{today}.html)</strong>을 다운로드 후 브라우저에서 열어보세요.</span>
        </td>
      </tr>

      <!-- 뉴스 섹션 -->
      <tr>
        <td style="padding:16px 28px 0">
          <div style="font-size:13px;font-weight:700;color:#1e40af;border-left:3px solid #1e40af;padding-left:10px;margin-bottom:8px">주요 뉴스</div>
        </td>
      </tr>
      <tr>
        <td style="padding:0 14px 8px">
          <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">
            {news_rows}
          </table>
        </td>
      </tr>

      <!-- 트렌드 섹션 -->
      <tr>
        <td style="padding:16px 28px 0">
          <div style="font-size:13px;font-weight:700;color:#5b21b6;border-left:3px solid #7c3aed;padding-left:10px;margin-bottom:8px">오늘의 트렌드</div>
        </td>
      </tr>
      <tr>
        <td style="padding:0 14px 16px">
          <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">
            {trends_rows if trends_rows else '<tr><td style="padding:10px 14px;color:#718096">첨부 파일 참조</td></tr>'}
          </table>
        </td>
      </tr>

      <!-- 푸터 -->
      <tr>
        <td style="background:#f8fafc;padding:14px 28px;border-top:1px solid #e2e8f0">
          <div style="font-size:11px;color:#9ca3af;text-align:center">Generated by Claude AI · {today} AI &amp; Data Daily Report</div>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def send_report(today: str) -> bool:
    """이메일 본문: Gmail 호환 요약 HTML / 첨부: 전체 리포트 HTML."""
    html_path = REPORT_DIR / f"{today}.html"
    md_path   = REPORT_DIR / f"{today}.md"
    if not html_path.exists():
        log.error(f"리포트 파일 없음: {html_path}")
        return False

    app_password = get_password()
    if not app_password:
        log.error("비밀번호를 찾을 수 없습니다. 'python scripts/setup_credential.py'를 먼저 실행하세요.")
        return False

    # 이메일 구성
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"[AI&Data 뉴스] {today} 일일 리포트"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAIL

    # 본문: Gmail 호환 요약 HTML
    body_html = build_email_body(today, md_path)
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # 첨부: 전체 리포트 HTML (브라우저에서 열기)
    attachment = MIMEBase("text", "html")
    attachment.set_payload(html_path.read_bytes())
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition", "attachment", filename=f"AIData_{today}.html"
    )
    msg.attach(attachment)

    # Gmail SMTP 발송
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(FROM_EMAIL, app_password)
            server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        log.info(f"이메일 발송 완료 → {TO_EMAIL}")
        return True
    except smtplib.SMTPAuthenticationError:
        log.error("Gmail 인증 실패. 앱 비밀번호를 확인하세요.")
        return False
    except Exception as e:
        log.error(f"이메일 발송 오류: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-only", action="store_true", help="INGEST 생략, 이메일 발송만 수행")
    parser.add_argument("--date", default=None, help="대상 날짜 (기본: 오늘, 형식: YYYY-MM-DD)")
    args = parser.parse_args()

    today = args.date or datetime.now().strftime("%Y-%m-%d")

    if not args.send_only:
        if not run_ingest(today):
            sys.exit(1)

    if not send_report(today):
        sys.exit(1)

    log.info("모든 작업 완료.")
