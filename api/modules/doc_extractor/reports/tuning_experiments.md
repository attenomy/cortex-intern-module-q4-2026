# OCR Tuning Experiments

Dataset: SROIE test split, 30 images.

Confidence thresholds are applied after OCR to filter words; they do not change Tesseract inference itself.

| Experiment | Median ms | P95 ms | Mean accepted words |
|---|---:|---:|---:|
| psm_3 | 521.7 | 971.65 | 106.23 |
| psm_4 | 453.14 | 737.3 | 106.9 |
| psm_6 | 518.15 | 907.72 | 118.9 |
| psm_11 | 489.71 | 934.33 | 117.57 |
| psm_12 | 753.09 | 1179.31 | 118.3 |
| psm_6_dpi300 | 449.55 | 923.6 | 118.9 |
| r512_conf50_none | 140.86 | 355.72 | 16.53 |
| r512_conf50_median_3x3 | 154.63 | 337.01 | 12.73 |
| r512_conf50_median_5x5 | 166.12 | 333.03 | 8.8 |
| r512_conf70_none | 131.93 | 336.07 | 9.87 |
| r512_conf70_median_3x3 | 159.48 | 356.61 | 7.97 |
| r512_conf70_median_5x5 | 155.57 | 338.04 | 4.53 |
| r512_conf85_none | 137.27 | 334.52 | 6.47 |
| r512_conf85_median_3x3 | 166.68 | 349.22 | 5.13 |
| r512_conf85_median_5x5 | 146.98 | 328.4 | 2.3 |
| r1024_conf50_none | 400.68 | 561.43 | 63.77 |
| r1024_conf50_median_3x3 | 401.96 | 610.74 | 47.8 |
| r1024_conf50_median_5x5 | 366.62 | 622.63 | 31.97 |
| r1024_conf70_none | 420.02 | 612.11 | 47.97 |
| r1024_conf70_median_3x3 | 376.31 | 599.86 | 36.57 |
| r1024_conf70_median_5x5 | 296.13 | 573.9 | 23.23 |
| r1024_conf85_none | 392.1 | 560.44 | 36.13 |
| r1024_conf85_median_3x3 | 346.01 | 608.59 | 26.5 |
| r1024_conf85_median_5x5 | 275.21 | 508.12 | 15.87 |
