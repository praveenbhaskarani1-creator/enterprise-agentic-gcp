---
document_id: POL-PRIV-001
title: Customer Data Access and Privacy
version: "1.0"
effective_date: 2026-01-01
classification: confidential
owner: Security and Privacy
---

# Customer Data Access and Privacy

Customer data must be accessed only for a specific support or operational need.
Responses must disclose only the minimum information necessary for that task.

Bulk exports of customer personally identifiable information are prohibited.
Payment credentials, authentication secrets, and private access tokens must
never be returned.

Customer-data lookups and approval decisions must be auditable. A suspected
privacy incident is Priority 1 and must be escalated to the security team.

The Customer Operations Agent is read-only and must refuse requests to bypass
access controls, reveal secrets, or export customer records in bulk.
