from __future__ import annotations

import io
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "ppt_assets"
SOURCE_COMMIT = "bc6166f"

NAVY = "#17324D"
BLUE = "#2F6BFF"
CYAN = "#3AA7B8"
TEAL = "#278A78"
AMBER = "#E4A11B"
LIGHT = "#EEF3F8"
MID = "#C8D5E3"
DARK = "#12202F"
GRAY = "#5D6B78"
WHITE = "#FFFFFF"


def configure() -> None:
    candidates = ["Malgun Gothic", "AppleGothic", "Noto Sans CJK KR", "DejaVu Sans"]
    available = {font.name for font in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = WHITE
    plt.rcParams["axes.facecolor"] = WHITE
    plt.rcParams["text.color"] = DARK
    plt.rcParams["axes.labelcolor"] = DARK


def git_csv(path: str) -> pd.DataFrame:
    raw = subprocess.check_output(
        ["git", "show", f"{SOURCE_COMMIT}:{path}"], cwd=ROOT
    ).decode("utf-8")
    return pd.read_csv(io.StringIO(raw))


def canvas(title: str, subtitle: str = "") -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(0.7, 8.35, title, fontsize=25, fontweight="bold", color=NAVY, va="top")
    if subtitle:
        ax.text(0.72, 7.83, subtitle, fontsize=12.5, color=GRAY, va="top")
    return fig, ax


def rounded_box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float,
                title: str, body: str, color: str = BLUE, face: str = WHITE,
                title_size: float = 14, body_size: float = 10.5) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.018,rounding_size=0.12",
        linewidth=1.8, edgecolor=color, facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(x + 0.25, y + height - 0.28, title, fontsize=title_size,
            fontweight="bold", color=color, va="top")
    ax.text(x + 0.25, y + height - 0.78, body, fontsize=body_size,
            color=DARK, va="top", linespacing=1.35)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18,
                                 linewidth=1.8, color=MID))


def footer(ax: plt.Axes, text: str) -> None:
    ax.text(0.72, 0.22, text, fontsize=8.5, color=GRAY, va="bottom")


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / name, dpi=180, facecolor=WHITE, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def method_pipeline() -> None:
    fig, ax = canvas(
        "CHUM: 입력 추가가 아니라 ‘실제 정보 유용성’을 감사한다",
        "대안 설명을 하나씩 통제한 뒤 event–channel 단위로 결론을 낸다",
    )
    boxes = [
        (0.7, "① 입력 통제", "F0  sensor-only\nF1  sensor+control\nF0-C  capacity-matched"),
        (3.8, "② 정상분포 대치", "정상 train-only LOO imputer\nresidual block sampling\nzero masking과 FPR 비교"),
        (6.9, "③ 조건별 보정", "validation-only threshold\n각 perturbation마다 재보정\ntest label 미사용"),
        (10.0, "④ 사건별 효과", "ΔAUROC · ΔAUPRC\nrun/event bootstrap CI\nseed 방향 · FPR guardrail"),
        (13.1, "⑤ 합의 판정", "TCN + Transformer consensus\nIG 보조 교차검증\n품질 gate 미달 셀 제외"),
    ]
    for index, (x, heading, body) in enumerate(boxes):
        rounded_box(ax, (x, 4.0), 2.25, 2.45, heading, body,
                    color=[NAVY, BLUE, CYAN, TEAL, NAVY][index], body_size=9.4)
        if index < len(boxes) - 1:
            arrow(ax, (x + 2.28, 5.22), (boxes[index + 1][0] - 0.08, 5.22))
    rounded_box(
        ax, (3.25, 1.25), 9.5, 1.65,
        "최종 산출물",
        "사건 × 제어 채널 × 시간 문맥 × 아키텍처 → 추가 탐지 정보의 재현 가능한 utility map",
        color=AMBER, face="#FFF8E8", title_size=15, body_size=13,
    )
    arrow(ax, (8.0, 3.95), (8.0, 2.95))
    footer(ax, "해석 경계: 예측 정보 유용성 ≠ 인과 효과 ≠ 물리적 root cause")
    save(fig, "01_CHUM_METHOD_PIPELINE.png")


def dataset_protocol() -> None:
    fig, ax = canvas(
        "두 데이터 환경, 같은 누수 방지 원칙",
        "TEP의 공정 fault에서 방법을 잠그고 HAI 21.03의 HIL attack에서 제한적 외부 지지를 확인",
    )
    rounded_box(
        ax, (0.8, 1.3), 6.8, 5.8, "TEP · Tennessee Eastman Process",
        "2,800 independent runs  |  28 faults\n41 XMEAS sensors  |  11 XMV controls\n\nSplit by run\n1,792 train  /  448 validation  /  560 test\n\nPreprocessing\n정상 train 기준 scaler · sliding windows\nvalidation 정상 점수로 threshold 보정\n\nRole\n주 방법 개발 · architecture consensus · 민감도 검증",
        color=BLUE, face="#F4F7FF", title_size=16, body_size=12,
    )
    rounded_box(
        ax, (8.4, 1.3), 6.8, 5.8, "HAI 21.03 · Hardware-in-the-Loop",
        "8 episodes  |  1,323,608 rows\n50 global attack events\n29 sensor targets  |  28 active control histories\n\nLeakage audit\ntrain–test exact overlap 43,202 train rows 제거\npoint role · attack target 수작업/코드 검증\n\nPreprocessing\ntrain-only scaling · episode/time separation\n\nRole\n전역 성능 + 직접 공격 channel의 외부 지지",
        color=TEAL, face="#F1FAF7", title_size=16, body_size=12,
    )
    ax.text(8.0, 4.2, "→", ha="center", va="center", fontsize=34, color=MID, fontweight="bold")
    footer(ax, "Source: repository split/audit manifests; corrected HAI v2 only. HAI v1은 feature-order bug로 무효화·제외.")
    save(fig, "02_DATASET_AND_SPLIT_PROTOCOL.png")


def tep_consensus() -> None:
    data = git_csv("outputs/final_evidence_validation/RECOMPUTED_G3_PRIMARY_CELLS.csv")
    data["cell"] = "F" + data.fault_id.astype(str) + "/XMV" + data.channel.astype(str)
    order = ["F4/XMV10", "F19/XMV7", "F19/XMV8", "F25/XMV2"]
    fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
    x = np.arange(len(order))
    width = 0.34
    for offset, architecture, color in [(-width / 2, "tcn", BLUE), (width / 2, "transformer", TEAL)]:
        part = data[data.architecture == architecture].set_index("cell").loc[order]
        bars = ax.bar(x + offset, part.mean_delta_auroc, width, label=architecture.upper(), color=color)
        for bar, value in zip(bars, part.mean_delta_auroc):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.009, f"+{value:.3f}",
                    ha="center", fontsize=11, fontweight="bold", color=color)
    ax.axhline(0.02, color=AMBER, linewidth=1.6, linestyle="--", label="material gate +0.02")
    ax.set_xticks(x, order, fontsize=13, fontweight="bold")
    ax.set_ylim(0, 0.34)
    ax.set_ylabel("Original − conditional replacement  ΔAUROC", fontsize=12)
    ax.set_title("TEP: 4개 핵심 event–channel이 두 아키텍처에서 모두 재현", loc="left",
                 fontsize=23, fontweight="bold", color=NAVY, pad=22)
    ax.text(0, 1.02, "각 셀 5/5 seeds 동일 방향 · hierarchical run CI 하한 > 0 · |ΔFPR| ≤ 0.00125",
            transform=ax.transAxes, fontsize=12, color=GRAY)
    ax.grid(axis="y", color=LIGHT, linewidth=1)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    fig.text(0.06, 0.03, "Source: final evidence recomputation at commit bc6166f; ΔAUROC is information-loss under normal-distribution conditional replacement.", fontsize=8.5, color=GRAY)
    fig.tight_layout(rect=[0.04, 0.06, 0.98, 0.93])
    save(fig, "03_TEP_ARCHITECTURE_CONSENSUS.png")


def sensitivity_ranges() -> None:
    data = pd.read_csv(OUT.parent.parent / "outputs" / "chum_primary_sensitivity" / "SENSITIVITY_ARCHITECTURE_CELL_SUMMARY.csv")
    data["label"] = data.architecture.str.upper() + " · F" + data.fault_id.astype(str) + "/XMV" + data.channel.astype(int).astype(str)
    data = data.sort_values(["fault_id", "channel", "architecture"], ascending=[False, False, True]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
    y = np.arange(len(data))
    colors = [BLUE if architecture == "tcn" else TEAL for architecture in data.architecture]
    ax.hlines(y, data.min_delta_auroc, data.max_delta_auroc, color=colors, linewidth=5, alpha=0.6)
    ax.scatter(data.median_delta_auroc, y, color=colors, s=100, zorder=3, edgecolor=WHITE, linewidth=1.5)
    for index, row in data.iterrows():
        ax.text(row.max_delta_auroc + 0.006, index,
                f"{row.min_delta_auroc:.4f}–{row.max_delta_auroc:.4f}",
                va="center", fontsize=10, color=colors[index], fontweight="bold")
    ax.axvline(0.02, color=AMBER, linewidth=1.7, linestyle="--")
    ax.text(0.022, 0.08, "material gate", transform=ax.get_xaxis_transform(),
            color=AMBER, fontsize=10, va="bottom")
    ax.set_yticks(y, data.label, fontsize=11)
    ax.set_xlim(0, 0.33)
    ax.set_xlabel("9개 설정의 ΔAUROC 범위  (block 5/10/20 × draws 1/3/10)", fontsize=12)
    ax.set_title("설정 민감도: 4/4 셀이 두 아키텍처에서 엄격 기준 통과", loc="left",
                 fontsize=23, fontweight="bold", color=NAVY, pad=22)
    ax.text(0, 1.02, "모든 architecture–cell에서 9/9 positive · 9/9 material · 9/9 CI positive · 9/9 FPR guardrail",
            transform=ax.transAxes, fontsize=12, color=GRAY)
    ax.grid(axis="x", color=LIGHT, linewidth=1)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(0.06, 0.03, "New locked sensitivity experiment, 390 model-condition tasks; no retraining; checkpoints seeds 42–46 reused.", fontsize=8.5, color=GRAY)
    fig.tight_layout(rect=[0.04, 0.06, 0.98, 0.93])
    save(fig, "04_PRIMARY_SENSITIVITY_RANGES.png")


def hai_support() -> None:
    global_delta = git_csv("outputs/final_evidence_validation/RECOMPUTED_HAI_GLOBAL_DELTAS.csv")
    channel = git_csv("outputs/final_evidence_validation/RECOMPUTED_HAI_CONDITIONAL_STABLE_CELLS.csv")
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=110, gridspec_kw={"width_ratios": [0.9, 1.25]})
    metrics = ["mean_delta_auroc", "mean_delta_auprc", "mean_delta_etaf1"]
    labels = ["AUROC", "AUPRC", "eTaF1"]
    x = np.arange(3)
    width = 0.34
    for offset, (_, row), color in zip([-width / 2, width / 2], global_delta.iterrows(), [BLUE, TEAL]):
        values = [row[metric] for metric in metrics]
        bars = axes[0].bar(x + offset, values, width, label=row.contrast, color=color)
        for bar, value in zip(bars, values):
            axes[0].text(bar.get_x() + bar.get_width() / 2, value + 0.0015, f"+{value:.3f}",
                         ha="center", fontsize=9.5, color=color, fontweight="bold")
    axes[0].set_xticks(x, labels, fontsize=12, fontweight="bold")
    axes[0].set_ylim(0, 0.046)
    axes[0].set_title("전역 탐지 성능", loc="left", fontsize=16, fontweight="bold", color=NAVY)
    axes[0].legend(frameon=False, loc="upper left")
    axes[0].grid(axis="y", color=LIGHT)
    axes[0].spines[["top", "right", "left"]].set_visible(False)
    channel = channel.sort_values("mean_delta_normalized_mean_event_score")
    labels2 = channel.attack_id + " / " + channel.feature
    bars = axes[1].barh(labels2, channel.mean_delta_normalized_mean_event_score, color=CYAN)
    for bar, value in zip(bars, channel.mean_delta_normalized_mean_event_score):
        axes[1].text(value + 0.004, bar.get_y() + bar.get_height() / 2, f"+{value:.3f}",
                     va="center", fontsize=10, color=NAVY, fontweight="bold")
    axes[1].set_xlim(0, 0.24)
    axes[1].set_title("직접 공격된 control channel", loc="left", fontsize=16, fontweight="bold", color=NAVY)
    axes[1].set_xlabel("normalized event-score loss after conditional replacement", fontsize=10)
    axes[1].grid(axis="x", color=LIGHT)
    axes[1].spines[["top", "right", "left"]].set_visible(False)
    fig.suptitle("HAI 21.03: 다른 HIL 환경에서도 제한적 외부 지지", x=0.055, y=0.96,
                 ha="left", fontsize=23, fontweight="bold", color=NAVY)
    fig.text(0.056, 0.905, "Corrected v2 · 모든 전역 차이는 3/3 seeds 동일 방향 · 5개 targeted cells도 3/3 방향 일치",
             fontsize=12, color=GRAY)
    fig.text(0.056, 0.03, "Interpretation: external support, not universal process-wise or causal validation. Source: final evidence recomputation at commit bc6166f.", fontsize=8.5, color=GRAY)
    fig.tight_layout(rect=[0.04, 0.07, 0.98, 0.88], w_pad=5)
    save(fig, "05_HAI_EXTERNAL_SUPPORT.png")


def professor_fit() -> None:
    data = pd.read_csv(OUT.parent / "professor_research" / "PROFESSOR_PUBLICATION_MATRIX_2024_2026_UNIQUE.csv")
    counts = data.primary_theme.value_counts()
    selected = pd.Series({
        "6G·네트워크 AI": int(counts.get("6G·네트워크 AI", 0)),
        "의료 AI": int(counts.get("의료 AI", 0)),
        "신뢰 AI·RAG·에이전트": int(counts.get("신뢰 AI·RAG·에이전트", 0)),
    })
    fig, ax = canvas(
        "왜 CHUM이 추현승 교수 연구실에 맞는가",
        "최근 연구의 응용축은 다르지만, 공통 방법론은 ‘문맥 활용 → 신뢰성 검증 → 시스템 의사결정’이다",
    )
    cards = [
        (0.8, "6G·네트워크 AI", selected.iloc[0], "시계열 traffic·mobility\n예측을 resource·handover\n결정으로 연결", BLUE),
        (5.55, "의료 AI", selected.iloc[1], "다중 데이터셋·backbone\n외부 일반화·feature\n근거를 반복 검증", TEAL),
        (10.3, "신뢰 AI·RAG·에이전트", selected.iloc[2], "context 선택·evidence\nnoise와 reliability를\n명시적으로 평가", CYAN),
    ]
    for x, title, count, body, color in cards:
        rounded_box(ax, (x, 4.15), 4.1, 2.7, title, body, color=color, face="#F7FAFC", title_size=15, body_size=11)
        ax.text(x + 3.45, 6.6, str(count), fontsize=26, color=color, fontweight="bold", ha="right", va="top")
    arrow(ax, (2.85, 4.0), (6.1, 2.8))
    arrow(ax, (7.6, 4.0), (8.0, 2.85))
    arrow(ax, (12.35, 4.0), (9.9, 2.8))
    rounded_box(
        ax, (4.25, 1.05), 7.5, 1.8, "CHUM의 제안 위치",
        "산업 시계열에서 추가 control context가 언제·어디서 실제 정보를 제공하는지\narchitecture·분포 교란·오경보를 통제해 감사",
        color=AMBER, face="#FFF8E8", title_size=16, body_size=12,
    )
    footer(ax, "Counts: official lab publication lists, 2024–2026, 65 unique titles; rule-coded from titles, not citation-weighted bibliometrics.")
    save(fig, "06_PROFESSOR_FIT_MAP.png")


def evidence_scorecard() -> None:
    fig, ax = canvas(
        "논문 집필 전 증거 패키지: 핵심 공격 경로를 모두 차단",
        "모든 PASS는 raw table 재계산과 사전 고정 gate를 기준으로 한다",
    )
    rows = [
        ("용량 효과인가?", "F1 vs F0-C", "PASS", "parameter gap 0.26% (HAI); event gain 반복"),
        ("특정 구조만의 현상인가?", "GRU · TCN · Transformer", "PASS", "TEP gain pattern + 4-cell two-architecture consensus"),
        ("비현실적 masking 효과인가?", "normal conditional replacement", "PASS", "imputer quality + condition calibration + FPR guardrail"),
        ("seed·run 우연인가?", "5/3 seeds + hierarchical CI", "PASS", "primary cells 5/5; HAI support 3/3"),
        ("고정 hyperparameter 의존인가?", "3 block × 3 draws", "PASS", "4/4 cells × 2 architectures; 9/9 strict settings"),
        ("외부 환경에서도 보이는가?", "HAI 21.03 corrected v2", "SUPPORT", "global metrics + 5 directly attacked channel cells"),
    ]
    y = 6.8
    for question, control, status, evidence in rows:
        ax.add_patch(FancyBboxPatch((0.8, y - 0.66), 14.4, 0.83,
                                    boxstyle="round,pad=0.01,rounding_size=0.08",
                                    edgecolor=MID, facecolor="#FAFCFE", linewidth=1))
        ax.text(1.05, y - 0.1, question, fontsize=11.5, fontweight="bold", color=NAVY, va="center")
        ax.text(5.2, y - 0.1, control, fontsize=10.5, color=GRAY, va="center")
        status_color = BLUE if status == "PASS" else AMBER
        ax.text(9.2, y - 0.1, status, fontsize=11, color=status_color, fontweight="bold", va="center")
        ax.text(10.55, y - 0.1, evidence, fontsize=9.5, color=DARK, va="center")
        y -= 0.95
    footer(ax, "남은 경계: 인과·물리적 root cause·모든 산업/네트워크로의 보편 일반화는 주장하지 않음.")
    save(fig, "07_EVIDENCE_SCORECARD.png")


def main() -> None:
    configure()
    OUT.mkdir(parents=True, exist_ok=True)
    method_pipeline()
    dataset_protocol()
    tep_consensus()
    sensitivity_ranges()
    hai_support()
    professor_fit()
    evidence_scorecard()
    manifest = pd.DataFrame(
        [
            ("01_CHUM_METHOD_PIPELINE.png", "5", "CHUM methodology pipeline"),
            ("02_DATASET_AND_SPLIT_PROTOCOL.png", "6", "datasets, split, leakage controls"),
            ("03_TEP_ARCHITECTURE_CONSENSUS.png", "9", "primary TEP effect sizes"),
            ("04_PRIMARY_SENSITIVITY_RANGES.png", "11", "new robustness experiment"),
            ("05_HAI_EXTERNAL_SUPPORT.png", "10", "external validation"),
            ("06_PROFESSOR_FIT_MAP.png", "2", "advisor/lab fit"),
            ("07_EVIDENCE_SCORECARD.png", "8 or 12", "claim-control evidence summary"),
        ],
        columns=["asset", "recommended_slide", "purpose"],
    )
    manifest.to_csv(OUT / "PPT_ASSET_MANIFEST.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
