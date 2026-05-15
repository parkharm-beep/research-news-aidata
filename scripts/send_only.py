"""오늘 MD 보고서 → HTML 생성 → 이메일 발송 (INGEST 건너뜀)"""
import sys
from datetime import datetime
from pathlib import Path

# ingest_and_send 모듈의 send_report, build_email_body 재사용
sys.path.insert(0, str(Path(__file__).parent))
from ingest_and_send import send_report, log, REPORT_DIR

today = datetime.now().strftime("%Y-%m-%d")

# HTML 파일이 없으면 템플릿으로 간단 생성
html_path = REPORT_DIR / f"{today}.html"
md_path   = REPORT_DIR / f"{today}.md"
tpl_path  = Path(__file__).parent.parent / "templates" / "report.html"

if not md_path.exists():
    log.error(f"MD 보고서 없음: {md_path}")
    sys.exit(1)

if not html_path.exists():
    import re
    md = md_path.read_text(encoding="utf-8")
    tpl = tpl_path.read_text(encoding="utf-8")

    # 뉴스 카드 파싱
    news_cards = ""
    cat_map = {"🏛️": ("pub", "국내 공공데이터"), "🌐": ("cross", "AI×데이터"), "🌍": ("global", "글로벌 인프라")}
    current_cat = ("cross", "AI×데이터")
    for m in re.finditer(r"### (🏛️|🌐|🌍)[^\n]*\n|### 뉴스\s+\d+\.\s+(.+?)\n(.*?)(?=### |## |\Z)", md, re.DOTALL):
        if m.group(1):
            for emoji, val in cat_map.items():
                if emoji in m.group(0):
                    current_cat = val
        elif m.group(2):
            title = m.group(2).strip()
            body  = m.group(3)
            url_m  = re.search(r"\*\*출처\*\*.*?\[.*?\]\((.+?)\)", body)
            outlet_m = re.search(r"\*\*출처\*\*.*?\[(.+?)\]", body)
            tags_m = re.search(r"\*\*태그\*\*:\s*(.+)", body)
            sum_m  = re.search(r"\*\*요약\*\*:\s*(.+?)(?=\n-|\Z)", body, re.DOTALL)
            ins_m  = re.search(r"\*\*인사이트\*\*:\s*(.+?)(?=\n-|\Z)", body, re.DOTALL)
            url    = url_m.group(1) if url_m else "#"
            outlet = outlet_m.group(1) if outlet_m else ""
            tags   = tags_m.group(1).strip() if tags_m else ""
            summ   = sum_m.group(1).strip().replace("\n", " ") if sum_m else ""
            ins    = ins_m.group(1).strip().replace("\n", " ") if ins_m else ""
            tag_html = " ".join(f'<span class="tag">{t.strip().strip("`")}</span>' for t in tags.split("`") if t.strip().strip("`"))
            cat_cls, cat_label = current_cat
            news_cards += f"""
<div class="card {cat_cls}">
  <div class="card-header">
    <span class="badge badge-{cat_cls}">{cat_label}</span>
    <span class="outlet">{outlet}</span>
  </div>
  <h3 class="card-title"><a href="{url}" target="_blank">{title}</a></h3>
  <div class="tags">{tag_html}</div>
  <p class="summary">{summ}</p>
  <div class="insight">{ins}</div>
</div>"""

    # 트렌드 파싱
    trends_html = ""
    for m in re.finditer(r"### 트렌드\s+\d+\.\s+(.+?)\n(.*?)(?=### |\Z)", md, re.DOTALL):
        tname = m.group(1).strip()
        desc  = re.sub(r"\*\*.*?\*\*:?\s*", "", m.group(2).split("\n")[0]).strip()
        trends_html += f'<div class="trend-item"><strong>{tname}</strong><p>{desc}</p></div>'

    # 종합 분석 파싱
    syn_m = re.search(r"## 3\. 종합 분석\n(.+)", md, re.DOTALL)
    synthesis_html = f"<p>{syn_m.group(1).strip()}</p>" if syn_m else ""

    html = tpl.replace("{{DATE}}", today)\
              .replace("{{NEWS_CARDS_HTML}}", news_cards)\
              .replace("{{TRENDS_HTML}}", trends_html)\
              .replace("{{SYNTHESIS_HTML}}", synthesis_html)

    html_path.write_text(html, encoding="utf-8")
    log.info(f"HTML 생성 완료: {html_path}")

# 이메일 발송
if not send_report(today):
    sys.exit(1)

log.info("모든 작업 완료.")
