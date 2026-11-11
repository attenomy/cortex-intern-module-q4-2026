# Dataset Distribution and Provenance Report
## Dataset Overview
- Total samples: 1,400
- Classes: 4
- Samples per class: 350
- Random seed: 42
- Duplicate samples removed: 0 (as recorded in manifest)
## Class Distribution
| Document Class | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Invoice | 244 | 52 | 54 | 350 |
| Receipt | 244 | 52 | 54 | 350 |
| Contract | 244 | 52 | 54 | 350 |
| Purchase Order | 244 | 52 | 54 | 350 |
| **Total** | **976** | **208** | **216** | **1,400** |
## Dataset Provenance
The original manifest lists the following claimed sources:
- Invoice: RVL-CDIP
- Receipt: SROIE / CORD
- Contract: CUAD
- Purchase Order: Public Purchase Order datasets
**Verification status: UNVERIFIED**
Original source records, download references, and sample-level provenance have not been independently established.
Representative images inspected from all four categories appear synthetic or template-generated. This observation does not independently establish the origin of every sample.
## Important Notes
- Do not describe this dataset as verified RVL-CDIP, SROIE, CUAD, or public PO data.
- Treat the current dataset as having unverified provenance.
- Existing model results must be described as results on the current held-out test split, not as benchmark results on the original public datasets.
- Authentic source dataset curation remains a separate task.
