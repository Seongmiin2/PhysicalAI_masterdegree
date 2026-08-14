# Mathematical Source Status

## 확인 원칙

이번 검토는 지정된 네 편만 대상으로 했다. 출판사 원문 또는 저자가 공개한 원문을 실제로 읽을 수 있을 때만 `FULL_TEXT_AVAILABLE`로 분류했다. 초록과 출판사 미리보기만 확인된 경우 수식, 목적함수, 방법 요소의 부재를 추정하지 않았다. PDF는 임시 작업 위치에서만 확인했으며 저장소에는 포함하지 않았다.

| 논문 | DOI / 공개 링크 | 상태 | 확인 범위 |
|:---|:---|:---:|:---|
| Chen et al. (2016), *Canonical correlation analysis-based fault detection methods with application to alumina evaporation process* | [DOI](https://doi.org/10.1016/j.conengprac.2015.10.006) | `ABSTRACT_ONLY` | 출판사 초록과 서지정보. static/dynamic CCA로 residual signal을 만든다는 설명까지만 확인했다. 원 수식, 목적함수, 시간처리의 부재는 확인하지 못했다. |
| Mercer, Martin & Morris (2002), *State-Space Residual Based Monitoring* | [DOI](https://doi.org/10.1016/S1570-7946(02)80149-3) | `ABSTRACT_ONLY` | 출판사 초록/목차 정보. state-space model mismatch와 output prediction residual을 PCA 통계로 감시한다는 범위까지만 확인했다. 원 수식은 확인하지 못했다. |
| Patel et al. (2018), *Adversarial Learning-Based On-Line Anomaly Monitoring for Assured Autonomy* | [DOI](https://doi.org/10.1109/IROS.2018.8593375), [author manuscript](https://arxiv.org/abs/1811.04539) | `FULL_TEXT_AVAILABLE` | 저자 공개 원문 전체. PDF pp. 1–6, Sections II–IV, Eqs. (1)–(2), Figs. 3–6 및 9–11을 확인했다. |
| Ji et al. (2024), *Incipient fault detection for dynamic processes with canonical variate residual statistics analysis* | [DOI](https://doi.org/10.1016/j.chemolab.2024.105189) | `ABSTRACT_ONLY` | 출판사 초록과 section snippets. CVDA의 CVR, sliding window statistics matrix, Mahalanobis index, FAR/FDR 평가까지만 확인했다. 상세 CVR 수식과 학습 목적함수는 확인하지 못했다. |

## 확보 결론

네 편 모두의 원문을 확보하지 못했다. 따라서 Chen, Mercer, Ji에 대해서는 `c_t`와 같은 두 예측 차이가 없다고 단정할 수 없고, 원 residual 수식이나 목적함수를 재구성할 수도 없다. 이 제한은 Mathematical Distinction Gate를 `INCONCLUSIVE`로 만드는 직접적인 중지 조건이다.
