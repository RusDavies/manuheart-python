# Product Process Classification

Status: Draft — not approved by existence.

## Governing process

This project follows the workspace Software Product Development Process in:

- `../guidance-docs-software-product/SOFTWARE_PRODUCT_DEVELOPMENT_PROCESS.md`
- `../guidance-docs-software-product/TAILORING_GUIDE.md`

## Target class

Target class: **Class 2 — Small Internal Tool**.

Russ specified the target class for this project as **internal tool**. Under the tailoring guide, this maps to Class 2: a small internal tool used by one person or a small trusted group, with limited blast radius and no public-facing release.

## Required lightweight artifacts

For this project, the process requires lightweight versions of:

- product/problem framing
- requirements or acceptance criteria
- UX/workflow notes, if a UI exists
- security/privacy notes
- architecture/deployment notes
- implementation checklist
- basic QA evidence
- rollback/disable note
- AI-agent operation boundary note, unless explicitly exempted by the product owner

## Approval boundaries

Human approval is required before:

- external actions
- destructive actions
- sensitive-data handling
- deployment into shared use
- accepted-risk decisions
- changes that materially alter product direction

## Current implication

Before implementation work is treated as complete, the project should capture at least minimal framing, requirements, security/privacy, architecture/deployment, QA evidence, rollback, and AI-agent-operation notes.
