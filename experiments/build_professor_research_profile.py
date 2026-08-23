from __future__ import annotations

import csv
import html
import re
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables" / "professor_research"
BASE = "http://monet.skku.edu/main/bbs/board.php"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 CHUM research audit"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean(fragment: str) -> str:
    fragment = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip(" .\t\r\n")


def classify(title: str) -> tuple[str, str, str]:
    lowered = title.lower()
    def has_any(terms: list[str]) -> bool:
        return any(
            re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered)
            for term in terms
        )

    themes: list[str] = []
    theme_rules = {
        "신뢰 AI·RAG·에이전트": [
            "rag", "retrieval", "evidence", "agent", "reporting", "llm",
            "collaborative ai", "curated collaborative", "inductive bias",
            "benchmarking", "reliable", "robust", "domain adaptation",
        ],
        "의료 AI": [
            "fundus", "retinal", "ophthalm", "medical", "rib", "respiratory",
            "cardiometabolic", "brain", "lesion", "glaucoma", "macular", "amd",
            "chest", "drug response", "visual field",
        ],
        "6G·네트워크 AI": [
            "network", "traffic", "b5g", "6g", "radio access", "ran", "mec",
            "handover", "uav", "mobile", "wireless", "iot", "aggregation",
            "resource localization", "edge",
        ],
        "산업·시계열 이상 진단": [
            "fault", "bearing", "battery", "diagnostic", "anomaly", "cyber",
            "air quality", "time series", "time-series",
        ],
    }
    for theme, terms in theme_rules.items():
        if has_any(terms):
            themes.append(theme)
    if not themes:
        themes.append("기타 응용 AI")

    method_rules = {
        "시계열": ["time series", "time-series", "temporal", "lstm", "tcn", "forecast", "prediction"],
        "멀티태스크·멀티모달": ["multi-task", "multitask", "multimodal", "multi-modal", "text-image-audio"],
        "Transformer·하이브리드": ["transformer", "hybrid", "residual", "architecture"],
        "그래프·강화학습": ["graph", "gcn", "reinforcement", "q-learning", "policy", "path planning", "scheduling"],
        "신뢰성·강건성": ["reliable", "robust", "domain", "drift", "inductive bias", "benchmark", "uncertainty", "confidence"],
        "생성형 AI·LLM": ["generative", "rag", "llm", "agent", "reporting"],
        "전처리·표현학습": ["clustering", "pruning", "feature", "representation", "segmentation"],
    }
    methods = [name for name, terms in method_rules.items() if has_any(terms)]
    return themes[0], "; ".join(themes), "; ".join(methods) or "응용 딥러닝"


def parse_publications(year: int, table: str, kind: str) -> list[dict[str, str | int]]:
    url = f"{BASE}?bo_table={table}&sca={year}"
    body = fetch(url)
    rows: list[dict[str, str | int]] = []
    for item in re.findall(r'<li class="">(.*?)</li>', body, flags=re.S):
        link = re.search(r'<a href="([^"]+)" class="bo_tit">(.*?)</a>', item, flags=re.S)
        if not link:
            continue
        title = clean(link.group(2))
        title = re.sub(r"^\d+\s*\.\s*", "", title)
        details = [clean(value) for value in re.findall(r"<dd>(.*?)</dd>", item, flags=re.S)]
        authors = details[0] if details else ""
        venue = details[1] if len(details) > 1 else ""
        primary, all_themes, methods = classify(title)
        rows.append(
            {
                "year": year,
                "list_type": kind,
                "title": title,
                "authors": authors,
                "venue": venue,
                "professor_author": "yes" if re.search(r"Hyunseung Choo|Hyun Seung Choo|추현승", authors, re.I) else "unclear",
                "primary_theme": primary,
                "all_themes": all_themes,
                "method_tags": methods,
                "record_url": html.unescape(link.group(1)),
                "source_list_url": url,
            }
        )
    return rows


def parse_projects() -> list[dict[str, str]]:
    url = f"{BASE}?bo_table=projects"
    body = fetch(url)
    rows: list[dict[str, str]] = []
    for item in re.findall(r'<li class="">(.*?)</li>', body, flags=re.S):
        link = re.search(r'<a href="([^"]+)" class="bo_tit">(.*?)</a>', item, flags=re.S)
        if not link:
            continue
        details = [clean(value) for value in re.findall(r"<dd>(.*?)</dd>", item, flags=re.S)]
        record_url = html.unescape(link.group(1))
        detail_body = fetch(record_url)
        subtitle_match = re.search(r'<p class="refer">(.*?)</p>', detail_body, flags=re.S)
        objective_match = re.search(
            r'<section id="bo_v_desc">(.*?)</section>', detail_body, flags=re.S
        )
        rows.append(
            {
                "project": clean(link.group(2)),
                "subtitle": clean(subtitle_match.group(1)) if subtitle_match else "",
                "period": details[0] if details else "",
                "agency": details[1] if len(details) > 1 else "",
                "objective": clean(objective_match.group(1)) if objective_match else "",
                "record_url": record_url,
                "source_list_url": url,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"No records parsed for {path.name}")
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    publications: list[dict[str, str | int]] = []
    for year in (2024, 2025, 2026):
        publications.extend(parse_publications(year, "public1", "lab_journal_list"))
        publications.extend(parse_publications(year, "public2", "lab_conference_list"))
    projects = parse_projects()
    write_csv(OUTPUT / "PROFESSOR_PUBLICATION_MATRIX_2024_2026.csv", publications)
    unique_by_title: dict[str, dict[str, str | int]] = {}
    for row in publications:
        key = re.sub(r"\W+", "", str(row["title"]).casefold())
        if key not in unique_by_title:
            unique_by_title[key] = row.copy()
        else:
            unique_by_title[key]["list_type"] = "both_lab_lists"
    unique_publications = list(unique_by_title.values())
    write_csv(
        OUTPUT / "PROFESSOR_PUBLICATION_MATRIX_2024_2026_UNIQUE.csv",
        unique_publications,
    )
    write_csv(OUTPUT / "LAB_PROJECT_MATRIX.csv", projects)

    by_year = Counter(int(row["year"]) for row in unique_publications)
    by_theme = Counter(str(row["primary_theme"]) for row in unique_publications)
    by_method: Counter[str] = Counter()
    for row in unique_publications:
        for method in str(row["method_tags"]).split("; "):
            by_method[method] += 1

    lines = [
        "# 추현승 교수·Superintelligence Lab 최근 연구 프로파일",
        "",
        "## 조사 범위와 판독 원칙",
        "",
        f"- 공식 연구실 publication 목록 2024–2026: 총 **{len(publications)}개 등록**, 제목 기준 **{len(unique_publications)}편**을 수집했다.",
        "- 공식 연구실 ongoing project 목록을 별도 수집했다.",
        "- 아래 분류는 제목 키워드를 이용한 재현 가능한 규칙 기반 코딩이며, 인용지수 분석이나 논문의 질 평가가 아니다.",
        "- 연구실 페이지의 Journal/Conference 분류와 실제 출판 유형이 일부 다를 수 있어 원래 목록 유형을 그대로 보존했다.",
        "",
        "## 연도별 등록 수",
        "",
        "| 연도 | 등록 수 |",
        "| ---: | ---: |",
    ]
    lines.extend(f"| {year} | {by_year[year]} |" for year in sorted(by_year))
    lines.extend(["", "## 1차 주제 분포", "", "| 주제 | 등록 수 |", "| --- | ---: |"])
    lines.extend(f"| {theme} | {count} |" for theme, count in by_theme.most_common())
    lines.extend(["", "## 반복 방법론 신호", "", "| 방법론 신호 | 제목 출현 수 |", "| --- | ---: |"])
    lines.extend(f"| {method} | {count} |" for method, count in by_method.most_common())
    lines.extend(
        [
            "",
            "## CHUM과의 직접 적합성 해석",
            "",
            "1. **산업·네트워크 시계열:** traffic, mobility, resource 상태처럼 시간 문맥을 예측과 운용 의사결정에 연결하는 연구가 반복된다.",
            "2. **신뢰성과 비교 설계:** architecture benchmark, domain robustness, evidence quality처럼 단일 모델 최고점보다 결과의 안정성과 근거를 분리해 확인하는 흐름이 있다.",
            "3. **AI-native control 연결:** 예측값을 handover·resource allocation·network analytics로 이어 실제 시스템 안정성이나 비용으로 평가하는 프로젝트가 진행 중이다.",
            "4. **의료 AI의 외부 일반화:** 다중 데이터셋·다중 backbone·cross-dataset 검증이 반복돼, CHUM의 2개 데이터 환경·3개 architecture·보수적 gate와 방법론적 궁합이 좋다.",
            "",
            "따라서 CHUM은 ‘산업 이상 탐지의 새 분류기’보다 **신뢰 가능한 context-utilization audit**로 제안하는 편이 연구실의 최근 방법론 취향과 더 직접적으로 맞는다.",
            "",
            "## 데이터 파일",
            "",
            "- `PROFESSOR_PUBLICATION_MATRIX_2024_2026.csv`: 제목·저자·게재처·주제·방법론 태그·원문 링크",
            "- `PROFESSOR_PUBLICATION_MATRIX_2024_2026_UNIQUE.csv`: Journal/Conference 목록 간 중복 제목을 제거한 분석용 표",
            "- `LAB_PROJECT_MATRIX.csv`: 진행 프로젝트·기간·주관기관·원문 링크",
            "",
            "## 공식 출처",
            "",
            "- http://monet.skku.edu/main/",
            "- http://monet.skku.edu/main/bbs/board.php?bo_table=public1&sca=2026",
            "- http://monet.skku.edu/main/bbs/board.php?bo_table=public2&sca=2026",
            "- http://monet.skku.edu/main/bbs/board.php?bo_table=projects",
            "- https://pure.skku.edu/en/persons/hyunseung-choo/",
        ]
    )
    (OUTPUT / "PROFESSOR_RESEARCH_TRENDS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
