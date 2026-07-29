# Agentic ERP Customer Operations Lab

## Purpose
The **Agentic ERP Customer Operations Lab** is an experimental environment for building, evaluating, and operating AI agents integrated into Enterprise Resource Planning (ERP) customer workflows on Google Cloud Platform (GCP).

## Synthetic Customer Operations Use Case
This lab models end-to-end customer operations workflows (such as customer inquiry resolution, order status verification, inventory availability checks, customer profile updates, and refund handling) using synthetic data. AI agents interact with enterprise data stores and microservices while adhering to strict governance and human-in-the-loop validation policies.

## Planned Architecture
The lab targets a modern enterprise architecture built on Google Cloud services and agentic frameworks:

- **PostgreSQL**: Primary transactional database (OLTP) storing synthetic ERP customer and operational data.
- **Datastream**: Serverless Change Data Capture (CDC) service replicating transactional database changes in real time.
- **Dataflow**: Managed stream processing engine for ingesting, filtering, and transforming CDC streams.
- **BigQuery**: Analytical data warehouse and lakehouse powering operational analytics and agent evaluation logs.
- **RAG Engine**: Retrieval-Augmented Generation platform providing domain knowledge and context retrieval for agents.
- **ADK (Agent Development Kit)**: Framework for constructing structured, tool-augmented AI agent workflows.
- **Agent Runtime**: Execution engine and hosting layer for running subagents and executing tool calls safely.
- **Agent Gateway**: Enterprise gateway providing API management, request routing, rate limiting, and security policy enforcement.
- **Cloud Run**: Serverless container platform for hosting lightweight microservices and webhook endpoints.
- **GKE (Google Kubernetes Engine)**: Managed Kubernetes environment for scalable agent workloads and backend microservices.

> [!NOTE]
> **Current Status Notice**: The project is currently at **Day 1 foundation** status. The components listed above represent planned architectural targets under active development. Unbuilt components do not currently exist in the codebase.

## Learning Objectives
- Design and evaluate autonomous and semi-autonomous AI agents for ERP customer operations.
- Construct real-time CDC data pipelines connecting PostgreSQL to BigQuery via Datastream and Dataflow.
- Integrate RAG capabilities for domain-specific knowledge lookup and contextual reasoning.
- Enforce strict agent safety guidelines, privacy standards (synthetic data), and human-in-the-loop approvals.
- Deploy and orchestrate containerized agent runtimes and microservices on Cloud Run and GKE.

## Repository Structure
- [app/](file:///home/praveen_bhaskarani1/agentic-erp-lab/app): Source code for microservices, Agent Gateway, and agent runtime implementations.
- [docs/](file:///home/praveen_bhaskarani1/agentic-erp-lab/docs): Architectural documentation, design specifications, and guides.
- [infra/](file:///home/praveen_bhaskarani1/agentic-erp-lab/infra): Infrastructure as Code (Terraform) and deployment manifests.
- [scripts/](file:///home/praveen_bhaskarani1/agentic-erp-lab/scripts): Utility scripts for development, data generation, and operational automation.
- [specs/](file:///home/praveen_bhaskarani1/agentic-erp-lab/specs): API specifications, data schemas, and agent tool contract definitions.
- [tests/](file:///home/praveen_bhaskarani1/agentic-erp-lab/tests): Unit, integration, security tests, and agent evaluation suites.
- [AGENTS.md](file:///home/praveen_bhaskarani1/agentic-erp-lab/AGENTS.md): Core rules, security guidelines, and privacy directives for AI agents.

## Environment & Configuration
- **Environment**: `dev`
- **Primary Region**: `us-central1`
- **Current Status**: Day 1 foundation

## Setup Instructions
Setup instructions will be added incrementally as infrastructure modules, database schemas, and agent components are developed and deployed.

## Cost & Security Warnings

> [!WARNING]
> **Cost Warning**: Provisioning infrastructure components in this architecture (such as GKE clusters, Cloud SQL / PostgreSQL instances, Datastream streams, Dataflow pipelines, and BigQuery datasets) incurs real Google Cloud billing costs. Ensure unused resources are deleted or scaled down when not actively testing.

> [!CAUTION]
> **Security & Data Privacy Rules**:
> - **Synthetic Data Only**: Do not ingest, process, or store real customer data or PII.
> - **Credentials Protection**: Never create, display, download, or commit service-account keys or credentials.
> - **Secrets & State Management**: Never commit `.env` files, database dumps, secrets, or Terraform state files.
> - **Authentication**: Use Application Default Credentials (ADC) and least-privilege service identities.
