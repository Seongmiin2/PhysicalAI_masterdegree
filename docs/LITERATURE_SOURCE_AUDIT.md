# Literature Source Audit

## 감사 원칙

기존 `LITERATURE_NOVELTY_GATE_PRELIMINARY.md`의 14개 항목을 처음부터 다시 확인했다. 출판사 페이지, IEEE/IFAC 또는 저자 공개 원문, 대학 연구 저장소, Crossref 계열 메타데이터 순으로 확인했다. 검색결과 요약이나 ResearchGate만으로 방법 세부를 확정하지 않았다.

검증 상태:

- `FULL_TEXT_VERIFIED`: 합법적으로 공개된 원문에서 방법을 확인함
- `ABSTRACT_VERIFIED`: 출판사 또는 공식 초록과 서지정보까지 확인함
- `METADATA_ONLY`: 제목·저자·연도·출처·DOI만 확인함
- `INVALID_OR_MISMATCHED`: 기존 표의 제목·저자·DOI 조합이 실제 논문과 불일치함

## 14개 항목 감사 결과

| 기존 # | 검증된 서지정보 | 공식 출처 | 상태 | 감사 결과 |
|---:|:---|:---|:---:|:---|
| 1 | A. Negiz, A. Çinar (1998), “Monitoring of multivariable dynamic processes and sensor auditing,” *Journal of Process Control*, 8(5–6), 375–380. DOI: [10.1016/S0959-1524(98)00006-7](https://doi.org/10.1016/S0959-1524(98)00006-7) | Elsevier/ScienceDirect | `ABSTRACT_VERIFIED` | 기존 제목·저자·DOI가 일치함. 폐루프 공정의 autocorrelation/cross-correlation/collinearity와 CV state model을 명시함. |
| 2 | E. L. Russell, L. H. Chiang, R. D. Braatz (2000), “Fault detection in industrial processes using canonical variate analysis and dynamic principal component analysis,” *Chemometrics and Intelligent Laboratory Systems*, 51(1), 81–93. DOI: [10.1016/S0169-7439(00)00058-7](https://doi.org/10.1016/S0169-7439(00)00058-7) | Elsevier/ScienceDirect | `ABSTRACT_VERIFIED` | 기존 서지 조합이 일치함. TEP에서 PCA/DPCA/CVA의 state/residual monitoring을 비교함. |
| 3 | Y. Wang, D. E. Seborg, W. E. Larimore (1997), “Process Monitoring Using Canonical Variate Analysis and Principal Component Analysis,” *IFAC Proceedings Volumes*, 30(9), 577–582. DOI: [10.1016/S1474-6670(17)43211-3](https://doi.org/10.1016/S1474-6670(17)43211-3) | IFAC/Elsevier 및 Seborg 공식 publication list | `ABSTRACT_VERIFIED` | 기존 본문에서 저자를 명시하지 않아 불완전했음. input-output data로 선형 stochastic state-space model을 식별함. |
| 4 | Z. Chen, S. X. Ding, K. Zhang, Z. Li, Z. Hu (2016), “Canonical correlation analysis-based fault detection methods with application to alumina evaporation process,” *Control Engineering Practice*, 46, 51–58. DOI: [10.1016/j.conengprac.2015.10.006](https://doi.org/10.1016/j.conengprac.2015.10.006) | Elsevier/ScienceDirect | `INVALID_OR_MISMATCHED` | 기존 표는 Jiang et al.로 잘못 연결함. 실제 저자는 Chen et al.이며 input-output CCA residual을 사용함. |
| 5 | E. Mercer, E. B. Martin, A. J. Morris (2002), “State-Space Residual Based Monitoring,” *Computer Aided Chemical Engineering*, 10, 727–732. DOI: [10.1016/S1570-7946(02)80149-3](https://doi.org/10.1016/S1570-7946(02)80149-3) | Elsevier/ScienceDirect | `ABSTRACT_VERIFIED` | 제목·저자·DOI가 일치함. CVA state-space model mismatch와 output prediction residual에 PCA statistics를 적용함. |
| 6 | T. J. Rato, M. S. Reis (2013), “Fault detection in the Tennessee Eastman benchmark process using dynamic principal components analysis based on decorrelated residuals (DPCA-DR),” *Chemometrics and Intelligent Laboratory Systems*, 125, 101–108. DOI: [10.1016/j.chemolab.2013.04.002](https://doi.org/10.1016/j.chemolab.2013.04.002) | Elsevier/ScienceDirect | `ABSTRACT_VERIFIED` | 기존 저자·제목·DOI가 일치함. control-conditioned model이 아니라 DPCA monitoring-statistic autocorrelation 완화가 목적임. |
| 7 | C. F. Alcala, R. Dunia, S. J. Qin (2012), “Monitoring of Dynamic Processes with Subspace Identification and Principal Component Analysis,” *IFAC Proceedings Volumes*, 45(20), 684–689. DOI: [10.3182/20120829-3-MX-2028.00238](https://doi.org/10.3182/20120829-3-MX-2028.00238) | IFAC/Elsevier 및 Lingnan University record | `INVALID_OR_MISMATCHED` | 기존 표는 Negiz et al.로 잘못 표기함. 실제 저자는 Alcala, Dunia, Qin이며 parity space statistics를 사용함. |
| 8 | G. Li, S. J. Qin, T. Yuan (2016), “Data-driven root cause diagnosis of faults in process industries,” *Chemometrics and Intelligent Laboratory Systems*, 159, 1–11. DOI: [10.1016/j.chemolab.2016.09.006](https://doi.org/10.1016/j.chemolab.2016.09.006) | Elsevier/ScienceDirect | `INVALID_OR_MISMATCHED` | 기존 표의 DOI `10.1016/j.chemolab.2016.11.007`은 이 논문과 일치하지 않음. 실제 논문은 fault 검출 후 DPCA/RBC와 causality analysis로 root cause를 찾는 진단 연구라 핵심 재검토에서 제외함. |
| 9 | M. A. Bin Shams, H. M. Budman, T. A. Duever (2011), “Fault detection, identification and diagnosis using CUSUM based PCA,” *Chemical Engineering Science*, 66(20), 4488–4498. DOI: [10.1016/j.ces.2011.05.028](https://doi.org/10.1016/j.ces.2011.05.028) | Elsevier/ScienceDirect | `INVALID_OR_MISMATCHED` | 기존 표는 Rato et al.로 잘못 표기함. 실제 저자는 Bin Shams, Budman, Duever이며 TEP의 CUSUM-PCA 누적 통계를 사용함. |
| 10 | Y. Du, D. Du (2018), “Fault Detection using Empirical Mode Decomposition based PCA and CUSUM with Application to the Tennessee Eastman Process,” *IFAC-PapersOnLine*, 51(18), 488–493. DOI: [10.1016/j.ifacol.2018.09.377](https://doi.org/10.1016/j.ifacol.2018.09.377) | IFAC/Elsevier 및 ADCHEM proceedings | `INVALID_OR_MISMATCHED` | 기존 표는 Dunia et al.로 잘못 표기함. 실제 저자는 Yuncheng Du, Dongping Du임. |
| 11 | K. Salahshoor, F. Kiasi (2008), “Online Statistical Monitoring and Fault Classification of the Tennessee Eastman Challenge Process Based on Dynamic Independent Component Analysis and Support Vector Machine,” *IFAC Proceedings Volumes*, 41(2), 7405–7412. DOI: [10.3182/20080706-5-KR-1001.01252](https://doi.org/10.3182/20080706-5-KR-1001.01252) | IFAC 공개 원문/Elsevier | `INVALID_OR_MISMATCHED` | 기존 표는 Lee et al.로 잘못 표기함. 실제 저자는 Salahshoor와 Kiasi이며 DICA-SVM 분류가 중심이어서 핵심 재검토에서 제외함. |
| 12 | N. Patel, A. N. Saridena, A. Choromanska, P. Krishnamurthy, F. Khorrami (2018), “Adversarial Learning-Based On-Line Anomaly Monitoring for Assured Autonomy,” *IEEE/RSJ IROS 2018*, 6149–6154. DOI: [10.1109/IROS.2018.8593375](https://doi.org/10.1109/IROS.2018.8593375) | IEEE 및 [arXiv author manuscript](https://arxiv.org/abs/1811.04539) | `INVALID_OR_MISMATCHED` | 기존 표는 Zhu et al.로 잘못 표기함. 실제 저자는 Patel et al.이며 actuator-command-conditioned video prediction을 사용함. 2020 확장판 DOI 10.1109/TIV.2020.2997025와 혼동하지 않음. |
| 13 | F. Pasqualetti, F. Dörfler, F. Bullo (2013), “Attack Detection and Identification in Cyber-Physical Systems,” *IEEE Transactions on Automatic Control*, 58(11), 2715–2729. DOI: [10.1109/TAC.2013.2266831](https://doi.org/10.1109/TAC.2013.2266831) | IEEE 및 [author manuscript](https://arxiv.org/abs/1202.6144) | `FULL_TEXT_VERIFIED` | 기존 서지 조합이 일치함. 공격 detectability의 이론 문헌이며 산업 고장 예측 학습과 직접 목적은 다름. |
| 14 | H. Ji, Q. Hou, Y. Shao, Y. Zhang (2024), “Incipient fault detection for dynamic processes with canonical variate residual statistics analysis,” *Chemometrics and Intelligent Laboratory Systems*, 252, 105189. DOI: [10.1016/j.chemolab.2024.105189](https://doi.org/10.1016/j.chemolab.2024.105189) | Elsevier/ScienceDirect | `INVALID_OR_MISMATCHED` | 기존 표의 첫 저자 Gao는 오류이며 Hongquan Ji가 제1저자임. CV residual sliding-window statistics를 감시함. |

## 감사 결론

- 14개 중 기존 표 그대로 신뢰 가능한 항목은 1, 2, 5, 6, 13뿐이다.
- 4, 7, 9, 10, 12, 14는 저자 또는 논문 연결 오류가 명확하다.
- 3은 저자 정보가 빠져 있었고, 8과 11은 서지 연결 및 연구 직접성이 부족하다.
- 따라서 기존 예비 문서는 연구 주장이나 인용에 사용할 수 없다.
- 후속 검토는 서지와 관련성이 검증된 9편으로 제한한다.
