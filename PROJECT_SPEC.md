# Rare Disease Diagnostic Agent — Project Specification

## Overview

This project explores the use of local large language models and retrieval-augmented reasoning to support clinicians in generating differential diagnoses for rare genetic diseases.

Rare diseases are frequently under-recognized due to their low prevalence and complex symptom patterns. The goal of this system is to assist clinicians by suggesting potential rare disease candidates based on patient phenotype information.

The system analyzes:

- Free-text clinical case descriptions
- Structured phenotype terms
- Optional genomic findings

The output is a ranked list of candidate rare diseases with explanations and supporting evidence retrieved from a curated knowledge base.

This project is implemented as a research prototype and is not intended for clinical deployment.

## Scope and Goals

The system is designed to assist clinicians in exploring possible rare disease diagnoses.

### Supported Inputs

The system accepts the following types of information:

- Free-text clinical narratives (e.g., history and physical notes)
- Structured phenotype terms such as HPO codes
- Patient demographics (age, sex)
- Family history
- Laboratory summaries
- Optional genetic findings (gene variants)

### System Outputs

The system generates:

- A ranked list of candidate rare diseases
- Short explanations for each candidate
- Key discriminating features supporting or contradicting each hypothesis
- Suggested follow-up questions or diagnostic tests
- Links to supporting evidence from the knowledge base

### Non-Goals

The system is not intended to:

- Provide a final medical diagnosis
- Recommend medications or treatments
- Provide emergency triage guidance
- Be used directly by patients without clinician oversight

  ## High-Level Architecture

The system consists of several core components:

1. Case ingestion service
2. Preprocessing and phenotype extraction
3. Medical knowledge base
4. Retrieval system
5. Local LLM reasoning module
6. Diagnostic agent orchestrator
7. User interface

These components work together to transform clinical case descriptions into a structured phenotype representation and generate a ranked differential diagnosis.
