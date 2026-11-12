# 🛡️ RAPPORT D'AUDIT MATINAL QUOTIDIEN — 2026-11-13

*Généré automatiquement le 2026-11-13 00:04:23 — Pipeline Batch Airflow / PostgreSQL*

| Indicateur | Valeur Mesurée |
| :--- | :--- |
| **Volume Transactions Analysées** | `3` |
| **Volume Financier Traité** | `930.89 €` |
| **Alertes Fraude Confirmées** | `1` (33.33 %) |
| **Montant Fraude Bloquée / Monitorée** | `825.81 €` |
| **Catégorie la Plus Ciblée** | `shopping_pos` |
| **Rejets Pandera / DLQ (`rejected/`)** | `0` |
| **Statut Data Drift (Gold)** | `OK` |

- **Stockage Data Lake Medallion** : `bronze/` -> `silver/` -> `gold/` & `rejected/`
- **Traçabilité OpenLineage** : `data_lake\lineage\openlineage_events.jsonl`
