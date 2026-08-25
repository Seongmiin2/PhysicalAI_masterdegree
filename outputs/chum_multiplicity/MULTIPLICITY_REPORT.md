# CHUM multiplicity report

## 분석 family와 분모

Primary family는 28개 fault와 LOO-residual imputer quality gate를 통과한
8개 channel의 Cartesian product인 **224개 candidate cell**이다. 원시
G3는 11개 archive channel, 즉 308개 cell을 모두 계산했지만 XMV5·XMV9는
상수이고 XMV4는 primary imputer quality gate를 통과하지 못해 confirmatory
family에서 제외했다. 제외 규칙은 효과크기가 아니라 대치 품질에만 근거한다.

## p-value와 BH-FDR

- 통계 단위: fault별 20개 held-out test run.
- 각 run에서 2 architectures × 5 seeds의 paired AUROC loss를 평균해 하나의
  run-cluster delta를 만들었다.
- 귀무가설은 run-cluster delta의 부호가 대칭이라는 것이다.
- 대립가설은 conditional replacement가 AUROC를 낮춘다는 단측 방향이다.
- 고정 seed의 paired sign-flip permutation을 200,000회 시행하고 add-one
  보정을 적용했다.
- 224개 p-value 전체에 Benjamini–Hochberg를 한 번 적용했다.

q=0.05 생존 cell은 **42/224**, q=0.10 생존 cell은 **48/224**다.
기존 locked 4개 중 q=0.05 생존은 **4/4**, q=0.10 생존은
**4/4**다.

| fault_id | channel | observed_mean_delta_auroc | p_value_one_sided | bh_q_value | bh_pass_q_0_05 | bh_pass_q_0_10 |
|---:|---:|---:|---:|---:|:---:|:---:|
| 4 | 10 | 0.135359 | 4.99998e-06 | 5.59997e-05 | True | True |
| 19 | 7 | 0.129473 | 4.99998e-06 | 5.59997e-05 | True | True |
| 19 | 8 | 0.0543213 | 4.99998e-06 | 5.59997e-05 | True | True |
| 25 | 2 | 0.276677 | 4.99998e-06 | 5.59997e-05 | True | True |

이 검정은 fixed TEP test distribution의 run-level 안정성을 다룬다. 5개
model seed를 독립 데이터셋으로 세지 않으며, 물리적 인과효과를 검정하지
않는다.

## 3중 필터 결합 확률

Locked cell은 ① 5/5 seed 양의 방향, ② TCN·Transformer 2/2 architecture
양의 방향, ③ 9/9 sensitivity 설정 양의 방향을 동시에 만족했다. 각 표결을
독립이고 귀무가설 아래 양/음 확률이 1/2라고 두는 **설명용 근사**에서는

`P(pass) = 2^-(5+2+9) = 0.0000152588`

이고, 224개 후보의 기대 통과 위양성 수는 **0.003418**, 적어도
하나가 우연히 통과할 확률 근사는 **0.003412**다.

그러나 seed, architecture, sensitivity 설정은 같은 데이터와 학습 계보를
공유하므로 독립 가정은 강하다. sensitivity 9개를 완전 의존으로 축약하면
동일 계산은 `2^-(5+2+1) = 0.00390625`, 기대 위양성 수
**0.875**까지 커진다.
architecture와 sensitivity 의존성을 모두 무시하고 seed 방향만 남기면
기대 위양성 수는 `224 / 32 = 7.0`이다. 따라서 이 결합 확률은 BH-FDR을
대체하는 유의확률이 아니라, 반복 필터가 얼마나 엄격한지 보여 주는
민감도 설명으로만 사용한다.

## 재현

`python experiments/analyze_chum_multiplicity.py`

원자료는 Git evidence commit `bc6166f`의 G3 cell/run tables이며,
복원된 `G3_CELL_RESULTS.csv`의 SHA-256과 분모는
`G3_SELECTION_MANIFEST.json`에 기록된다.
