# CHUM primary sensitivity preregistration audit

## 판정

**`POST_HOC_UNIFORM_RULE — 사전등록으로 주장하지 않음`**

민감도 실험의 설정, 판정 규칙, 분석 코드, 결과 CSV는 Git 이력에서 모두
같은 커밋에 처음 나타난다. 따라서 임계값이 결과 생성 전에 외부적으로
고정되었다는 사실을 저장소 이력만으로 입증할 수 없다.

이 판정은 결과가 무효라는 뜻이 아니다. 네 locked cell과 두 architecture,
9개 sensitivity 설정 전체에 동일한 기준을 적용했다는 robustness 분석으로
보고하되, confirmatory preregistration 또는 prospective registration으로
부르지 않는다.

## Git 근거

다음 파일은 모두 커밋 `63771cc93884f3d2a26f0fa69055bb0995402814`
(`2026-08-24T00:28:14+09:00`, `Complete CHUM experiments and
professor-ready proposal`)에서 처음 추가되었다.

| 파일 | Git 최초 커밋 |
|---|---|
| `configs/architecture_chum_sensitivity.yaml` | `63771cc` |
| `experiments/run_architecture_chum_sensitivity.py` | `63771cc` |
| `experiments/analyze_architecture_chum_sensitivity.py` | `63771cc` |
| `outputs/chum_primary_sensitivity/SENSITIVITY_DECISION.json` | `63771cc` |
| `outputs/chum_primary_sensitivity/SENSITIVITY_RUN_RESULTS.csv` | `63771cc` |
| `outputs/chum_primary_sensitivity/SENSITIVITY_CELL_RESULTS.csv` | `63771cc` |

재현 명령:

```powershell
git log --follow --reverse --format="%H|%aI|%s" -- configs/architecture_chum_sensitivity.yaml
git log --follow --reverse --format="%H|%aI|%s" -- outputs/chum_primary_sensitivity/SENSITIVITY_DECISION.json
git log --follow --reverse --format="%H|%aI|%s" -- outputs/chum_primary_sensitivity/SENSITIVITY_RUN_RESULTS.csv
```

`SENSITIVITY_RUN_MANIFEST.json`은 config SHA-256
`154985ba0c5829bbee39f34cfd284ebacbf4ffdf13e49e44ddcbb47a9d4cab6e`가
실행 시작과 종료 시 동일했음을 기록한다. 이는 **실행 도중 설정이 바뀌지
않았다는 무결성 근거**지만, 설정이 결과 관찰 전에 커밋되었다는
사전등록 근거는 아니다. 설정 파일의 `Locked before execution` 주석도
독립적인 시점 증명이 아니므로 사전등록 판정에 사용하지 않았다.

## 동일 적용된 post-hoc 규칙

다음 규칙은 결과 공개 후 임의의 셀만 골라 다르게 적용하지 않고, 네 locked
cell × 두 architecture × 9개 설정 전체에 동일하게 적용되었다.

- positive mean delta AUROC: 9/9 settings
- material delta AUROC `>= 0.02`: 최소 8/9 settings
- positive model seeds: `>= 4/5`: 최소 8/9 settings
- paired hierarchical run CI 하한 `> 0`: 최소 8/9 settings
- absolute pre-fault FPR shift `<= 0.005`: 9/9 settings
- reference setting block 20 / draws 3: 모든 setting-level gate 통과
- 전체 PASS: 4/4 locked cell에서 TCN과 Transformer 모두 robust

## 보고 경계

- 허용 표현: “post-hoc robustness rule applied uniformly to every locked
  architecture-cell and sensitivity setting.”
- 금지 표현: “preregistered”, “prospectively registered”, “사전등록 기준”.
- 다중비교 방어는 별도의 224-cell BH-FDR 결과를 우선 사용한다.
- 3중 반복 필터 결합 확률은 의존성 가정에 민감한 설명용 민감도 분석이며,
  BH-FDR을 대체하지 않는다.
