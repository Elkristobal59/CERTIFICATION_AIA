# 🛡️ RAPPORT D'AUDIT MATINAL QUOTIDIEN — 2026-11-14

*Généré automatiquement le 2026-11-14 00:08:17 — Pipeline Batch Airflow / PostgreSQL*

| Indicateur | Valeur Mesurée |
| :--- | :--- |
| **Volume Transactions Analysées** | `9` |
| **Volume Financier Traité** | `2882.17 €` |
| **Alertes Fraude Confirmées** | `3` (33.33 %) |
| **Montant Fraude Bloquée / Monitorée** | `2429.14 €` |
| **Catégorie la Plus Ciblée** | `entertainment` |
| **Rejets Pandera / DLQ (`rejected/`)** | `0` |
| **Statut Data Drift (Gold)** | `OK` |

- **Stockage Data Lake Medallion** : `bronze/` -> `silver/` -> `gold/` & `rejected/`
- **Traçabilité OpenLineage** : `data_lake\lineage\openlineage_events.jsonl`
