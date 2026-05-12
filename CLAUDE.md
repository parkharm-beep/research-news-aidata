# AI & Data Daily News Wiki — Schema (CLAUDE.md)

## 프로젝트 개요

매일 아침 AI와 데이터 관련 최신 뉴스를 수집하고, 구조화된 지식 베이스(Wiki)를 누적하며,
가독성 높은 HTML 보고서를 생성하는 자동화 뉴스 큐레이션 시스템.

Karpathy의 LLM Wiki 패턴을 따름:
- **sources/** — 원본 수집 기사 (날짜별 불변 보관)
- **wiki/** — LLM이 유지·관리하는 구조화된 지식 베이스
- **reports/** — 매일 생성되는 마크다운 보고서(`.md`) + 온톨로지 그래프 시각화(`.html`)
- **index.md** — 전체 콘텐츠 카탈로그 (확인 상태 포함)
- **log.md** — 작업 이력 (append-only)

---

## 디렉토리 구조

```
AIData_News/
├── CLAUDE.md              ← 이 파일 (스키마 & 운영 지침)
├── index.md               ← 전체 콘텐츠 카탈로그
├── log.md                 ← 작업 로그 (append-only)
├── sources/               ← 날짜별 원본 기사 데이터
│   └── YYYY-MM-DD/
│       └── raw_NNN.md
├── wiki/                  ← 누적 지식 베이스
│   ├── topics/            ← 주제별 페이지 (LLM, 데이터파이프라인 등)
│   └── trends/            ← 트렌드 추적 페이지
├── reports/               ← 날짜별 보고서 (두 포맷)
│   ├── YYYY-MM-DD.md      ← 마크다운 보고서 (읽기용, 1차 산출물)
│   └── YYYY-MM-DD.html    ← 스타일드 HTML 보고서 (카드형, report.html 템플릿 사용)
└── templates/
    ├── report.md.tpl      ← 마크다운 보고서 템플릿
    ├── graph.html.tpl     ← 온톨로지 그래프 D3.js 템플릿 ({{DATE}}/{{NODES_JSON}}/{{EDGES_JSON}} 채워서 사용)
    └── report.html        ← 스타일드 HTML 보고서 템플릿 (선택적 사용)
```

---

## 파일명 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| wiki/topics/ | 한국어, 붙여쓰기, 구분 필요 시 `-` | `AI인프라-데이터센터.md` |
| wiki/trends/ | 한국어, 붙여쓰기, 구분 필요 시 `-` | `데이터거버넌스부채.md` |
| sources/ | `raw_NNN.md` (3자리 zero-pad) | `raw_001.md` |
| reports/ | `YYYY-MM-DD.md` / `.html` | `2026-05-11.md` |
| title 프론트매터 | 한국어 (기술 용어 영문 병기 허용) | `title: AI 인프라·데이터센터` |

**트렌드 상태 기준 (`status` 필드)**

| 상태 | 기준 |
|------|------|
| `emerging` | 1~2개 기사에서 처음 신호 감지 |
| `active` | 3개 이상 기사 또는 주요 기업의 전략적 행동으로 확인됨 |
| `declining` | 최근 30일간 관련 기사 없음 |

---

## 핵심 작업 (Operations)

### 1. INGEST — 일일 뉴스 수집 및 보고서 생성

**트리거**: 사용자가 "오늘 리포트 만들어줘" 또는 "뉴스 수집해줘"라고 요청할 때

**절차**:

1. **날짜 확인**: 오늘 날짜(YYYY-MM-DD) 확인
2. **뉴스 검색**: WebSearch로 다음 쿼리를 사용 (총 10개 내외 수집, 최신순)

   **소스 제한 (필수)**: WebSearch 호출 시 반드시 `allowed_domains` 파라미터를 아래 "승인된 뉴스 소스" 목록의 도메인으로 제한한다. 목록 외 사이트의 기사는 수집하지 않는다.

   **[0순위] 키워드 부스팅 검색** (발견 시 즉시 최우선 선정)
   - 쿼리: `"AI-Ready Data" OR "AI 친화적 데이터" OR "AI레디 데이터"`
   - 쿼리: `온톨로지 AI 데이터 OR "Knowledge Graph" AI`
   - 쿼리: `지식그래프 인공지능 OR "knowledge graph" artificial intelligence`
   - allowed_domains: 전체 승인 소스 (그룹 A+B+C+D)
   - 발견된 기사는 순위·정원에 관계없이 최우선 포함

   **[1순위] 국내 공공데이터 × AI 뉴스** (3~4개 목표)
   - 쿼리: `공공데이터 인공지능 AI 활용`
   - 쿼리: `공공데이터 개방 AI 서비스`
   - allowed_domains: 국내 IT 미디어 + 국내 공공기관 소스 그룹
   - 대상: 정부·지자체·공공기관의 AI 활용, 공공데이터 개방·연계, 공공 AI 서비스 출시

   **[2순위] 국내외 AI × 데이터 교차 뉴스** (4~5개 목표)
   - 쿼리: `인공지능 데이터 AI data`
   - 쿼리: `AI data governance enterprise`
   - allowed_domains: 국내 IT 미디어 + 해외 IT 미디어 소스 그룹

   **[3순위] 글로벌 AI 인프라·리포트** (2~3개 목표)
   - 쿼리: `AI infrastructure data investment report`
   - allowed_domains: 리포트·시장분석 + 해외 IT 미디어 소스 그룹

   **발행일 필터 (필수)**: 수집 대상은 **어제 09:00 ~ 오늘 09:00 사이에 발행된 기사만** 포함. 기사 URL·날짜 메타데이터로 발행일을 반드시 확인하고, 날짜 불명확 또는 범위 초과 기사는 제외.

   **AI+Data 교차 주제 선택 기준**: AI 기술/서비스가 데이터 수집·저장·처리·거버넌스에 직접 영향을 미치거나, 데이터 인프라가 AI 성능/확산에 영향을 미치는 기사. 순수 AI 연구(논문)나 순수 데이터베이스 기사는 제외.

   **키워드 우선순위 부스팅**: 수집 후 아래 키워드가 제목·본문에 포함된 기사는 다른 기사보다 **먼저 선정**한다. 10개 정원이 차더라도 부스팅 키워드 기사는 일반 기사 1개를 밀어내고 포함시킨다.
   | 키워드 | 한국어 변형 포함 |
   |--------|----------------|
   | `AI-Ready Data` | `AI 친화적 데이터`, `AI레디`, `AI 준비 데이터` |
   | `온톨로지` | `Ontology`, `지식 온톨로지` |
   | `지식그래프` | `Knowledge Graph`, `지식 그래프` |

   **부스팅 기사 시각 표식**: 0순위 키워드로 선정된 기사는 보고서에서 아래와 같이 표시한다.
   - 뉴스 제목에 `⭐` 접두어 추가 (예: `### 뉴스 9. ⭐ Neo4j, Gen AI 코파일럿으로...`)
   - 인사이트 첫 줄에 `🔑 **[키워드 부스팅]**` 접두어 추가
3. **sources/ 저장**: `sources/YYYY-MM-DD/raw_NNN.md` 형식으로 원본 저장
4. **마크다운 보고서 생성**: `reports/YYYY-MM-DD.md` 생성 (아래 마크다운 형식 참고)
5. **HTML 보고서 생성**: `reports/YYYY-MM-DD.html` 생성 (아래 HTML 리포트 생성 규칙 참고)
6. **wiki 업데이트** (신규/기존 페이지 분리 처리):
   a. 각 기사의 `topics:` 태그에서 주제 추출; 보고서의 트렌드 섹션에서 트렌드 추출
   b. `wiki/topics/`, `wiki/trends/` 에서 해당 파일 존재 여부 확인
   c. **파일 없음** → CLAUDE.md 하단 "Wiki 페이지 형식"에 맞춰 신규 생성
   d. **파일 있음** → 해당 날짜 행을 "최근 동향" 테이블에 append; `last_updated` 갱신
7. **index.md 업데이트** (두 위치 각각):
   - **일일 보고서 테이블**: 새 날짜 행 추가 (`.md` + `.html` 링크, 주요 키워드)
   - **Wiki 섹션**: 6단계에서 신규 생성된 페이지만 추가 (기존 링크 중복 기재 금지)
8. **log.md 기록**: 작업 결과 append

**INGEST 완료 기준** (이 모든 항목이 충족되면 완료):
- [ ] 수집된 모든 기사의 `published_at`이 어제 09:00 ~ 오늘 09:00 범위 내임을 확인
- [ ] `sources/YYYY-MM-DD/raw_001.md` ~ `raw_0NN.md` 생성됨 (10개 내외)
- [ ] `reports/YYYY-MM-DD.md` 생성됨
- [ ] `reports/YYYY-MM-DD.html` 생성됨 (report.html 템플릿 기반 카드형)
- [ ] 등장한 모든 주제·트렌드의 wiki 페이지 생성 또는 업데이트됨
- [ ] `index.md` 일일 보고서 테이블에 새 행 추가됨
- [ ] 신규 wiki 페이지가 `index.md` Wiki 섹션에 반영됨
- [ ] `log.md`에 작업 결과 append됨

**원본 파일 형식** (`sources/YYYY-MM-DD/raw_NNN.md`):

> **필수**: `published_at`는 반드시 기재. 기사 URL·날짜 메타데이터에서 확인 후 작성. 불명확 시 기사 제외.

```markdown
---
date: YYYY-MM-DD
published_at: YYYY-MM-DD HH:MM  ← 필수. 기사 원문 발행 시각 (어제 09:00 ~ 오늘 09:00 범위 검증)
source_url: https://...
title: 기사 제목
outlet: 매체명
collected_at: YYYY-MM-DD HH:MM
---

## 원문 요약
(3줄 이내 요약)

## AI-Data 인사이트
(AI와 데이터의 상호작용 핵심 포인트)

## 태그
topics: [LLM, 데이터파이프라인, ...]
companies: [OpenAI, Google, ...]
```

---

### 2. QUERY — 지식 베이스 검색 및 분석

**트리거**: 사용자가 특정 주제, 기업, 기간에 대해 질문할 때

**절차**:
1. `wiki/` 내 관련 페이지 검색
2. `sources/` 원본에서 증거 확인
3. 답변 + 출처 인용 제공
4. **wiki 업데이트 범위**: 기존 wiki 페이지의 "핵심 인사이트" 또는 "관련 기업/주제" 섹션에만 append 가능. 신규 wiki 페이지 생성 금지. QUERY 중 sources/ 수정 금지.

---

### 3. LINT — 지식 베이스 감사

**트리거**: 사용자가 "wiki 정리해줘" 또는 주간/월간 점검 요청 시

**수행 내용**:
- 오래된 트렌드 페이지 상태(`active`→`declining`) 검토 및 업데이트
- 고아 페이지(index.md에 링크 없거나 cross-reference 없는 페이지) 감지
- 모순된 정보 플래그 (동일 기업·주제 내 날짜별 사실 충돌)
- index.md 누락 항목 보충

**LINT 완료 기준** — 다음 형식의 감사 리포트를 사용자에게 출력:
```
## LINT 결과 — YYYY-MM-DD
- 점검 페이지: N개 (topics N, trends N)
- 상태 변경: [trending/declining 변경 목록]
- 고아 페이지: [목록 또는 "없음"]
- 모순 플래그: [목록 또는 "없음"]
- index.md 보충: [추가된 항목 또는 "없음"]
```

---

## 마크다운 보고서 형식 (`reports/YYYY-MM-DD.md`)

```markdown
# 📅 YYYY-MM-DD AI & Data Daily Report

> 큐레이터: Claude AI | 수집 기준: YYYY-MM-DD | 출처: N개 매체

## 1. 주요 뉴스 요약

### 🏛️ 국내 공공데이터 × AI

### 뉴스 N. [제목]
- **출처**: [매체명](URL)
- **태그**: `태그1` `태그2`
- **관련 기업**: 기업명 (없으면 생략)
- **요약**: (3줄)
- **인사이트**: (AI-Data 상호작용 핵심)

---

### 🌐 AI × 데이터 교차

### 뉴스 N. [제목]
- **출처**: [매체명](URL)
- **태그**: `태그1` `태그2`
- **관련 기업**: 기업명 (없으면 생략)
- **요약**: (3줄)
- **인사이트**: (AI-Data 상호작용 핵심)

---

### 🌍 글로벌 AI 인프라·거버넌스

### 뉴스 N. [제목]
- **출처**: [매체명](URL)
- **태그**: `태그1` `태그2`
- **관련 기업**: 기업명 (없으면 생략)
- **요약**: (3줄)
- **인사이트**: (AI-Data 상호작용 핵심)

## 2. 오늘의 인사이트 & 트렌드

### 트렌드 N. [트렌드명]
설명...

## 3. 종합 분석
전체 흐름 분석...
```

---

## HTML 리포트 생성 규칙 (`reports/YYYY-MM-DD.html`)

**생성 방법**: `templates/report.html`을 복사한 뒤 `{{DATE}}`, `{{NEWS_CARDS_HTML}}`, `{{TRENDS_HTML}}`, `{{SYNTHESIS_HTML}}` 플레이스홀더를 채운다.

**구조**: 날짜 헤더 → 수집 통계 → 카테고리별 뉴스 카드 섹션 → 트렌드 섹션 → 종합 분석. 온톨로지 그래프 불사용.

### 뉴스 카드 필수 항목
- 제목 (기사 URL 링크)
- 카테고리 배지 (`국내 공공데이터`, `AI×데이터`, `글로벌 인프라`)
- 출처·발행일시
- 태그
- 3줄 요약
- 인사이트 (강조 블록)

### 트렌드 카드 필수 항목
- 트렌드명 + 상태 배지 (`emerging` / `active` / `declining`)
- 한 줄 설명
- 관련 기사 수

---

## Wiki 페이지 형식

### topics/XXX.md
```markdown
---
title: 주제명
type: topic
last_updated: YYYY-MM-DD
related: [회사명, 다른주제]
---

## 개요
## 최근 동향
| 날짜 | 이벤트 | 출처 |
## 핵심 인사이트
## 관련 보고서
```

### trends/XXX.md
```markdown
---
title: 트렌드명
type: trend
status: active|emerging|declining
last_updated: YYYY-MM-DD
---

## 트렌드 설명
## 근거 데이터
## 관련 주제
## 전망
```

---

## log.md 기록 형식

```
## YYYY-MM-DD HH:MM — INGEST
- 수집 기사 수: N개
- 신규 wiki 페이지: [목록 또는 "없음"]
- 업데이트된 wiki 페이지: [목록 또는 "없음"]
- 보고서: reports/YYYY-MM-DD.md / reports/YYYY-MM-DD.html
```

---

## 운영 규칙

1. **sources/ 파일은 절대 수정하지 않는다** (불변 원본 보존)
2. **log.md는 항상 append** (기존 내용 삭제 금지)
3. **wiki 업데이트는 출처 명시** (sources/ 파일 경로 또는 URL 인용)
4. **HTML 보고서**: D3.js CDN(`jsdelivr`) 사용 허용. 그 외 CSS·JS는 인라인으로 포함해 파일 단독 실행 가능하게 유지
5. **모든 텍스트는 한국어** (기술 용어 영문 병기 허용)
6. **보고서 중복 방지**: 같은 날짜 보고서가 이미 있으면 사용자에게 확인 후 덮어쓰기
7. **소스 제한**: INGEST 수집은 반드시 아래 "승인된 뉴스 소스" 도메인 내에서만 수행
8. **index.md 확인 상태 관리**:
   - `확인` 컬럼 값: 비어있음(미확인) / `✅ YYYY-MM-DD`(확인완료) / `🔄`(갱신됨—재확인 필요)
   - INGEST 시 wiki 페이지를 업데이트하면, 해당 행의 `확인`이 `✅`이면 반드시 `🔄`로 변경
   - 새로 추가되는 일일 보고서 행과 신규 wiki 행의 `확인`은 빈칸으로 시작
   - 사용자가 "OOO 확인했어" 라고 하면 해당 행을 `✅ YYYY-MM-DD`로 업데이트

---

## 승인된 뉴스 소스

WebSearch 호출 시 `allowed_domains` 파라미터에 아래 도메인을 사용한다.

### 그룹 A — 국내 IT 미디어 (1·2순위 검색에 사용)
```
itworld.co.kr, zdnet.co.kr, etnews.com, ddaily.co.kr, bloter.net,
yozm.wishket.com, techm.kr, outstanding.kr, news.hada.io,
ttimes.co.kr, byline.network, dt.co.kr, newstomato.com, econovill.com
```

### 그룹 B — 해외 IT 미디어 (2·3순위 검색에 사용)
```
theverge.com, techcrunch.com, wired.com, engadget.com, arstechnica.com,
technologyreview.com, news.ycombinator.com, spectrum.ieee.org,
theregister.com, cnet.com, techradar.com, venturebeat.com,
businessinsider.com, zdnet.com
```

### 그룹 C — 리포트·시장분석 (3순위 검색에 사용)
```
gartner.com, idc.com, forrester.com, statista.com, spri.kr,
kisa.or.kr, nia.or.kr, mckinsey.com, deloitte.com, cbinsights.com
```

### 그룹 D — 국내 공공기관·테크블로그 (1순위 검색에 사용)
```
spri.kr, kisa.or.kr, nia.or.kr, korea.kr, mois.go.kr,
tech.kakao.com, d2.naver.com, toss.tech,
stackoverflow.blog, netflixtechblog.com, aws.amazon.com,
ai.googleblog.com, github.com
```

### 순위별 allowed_domains 조합
| 순위 | 사용 그룹 |
|------|----------|
| 1순위 (공공데이터×AI) | 그룹 A + 그룹 D |
| 2순위 (AI×데이터 교차) | 그룹 A + 그룹 B |
| 3순위 (글로벌 인프라·리포트) | 그룹 B + 그룹 C |
