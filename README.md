# Cheyenne and Laramie County cross-domain research engine

This is a scheduled, bounded public-record research worker, not an error-free autonomous investigator. It reads a public snapshot of bartimoussmith-oss/cheyenne-laramie-archive without executing source-repository code or modifying that archive. It does not ingest private research, credentials, scanner archives or resident dossiers.

## Scale, stated accurately
36 civic subjects yield 630 unordered subject pairs. Sixteen recipe specifications yield 10,080 generated research-plan combinations: 720 times the fourteen topical profiles. This is a combinatorial research catalog, NOT 10,080 distinct implemented algorithms, completed investigations or discoveries. Four algorithms are implemented, producing 2,520 eligible pair/recipe variants. The twelve other recipe types stay implemented=false and are not executed. Financial reconciliation, spatial joins, legal obligations and causal claims require additional reviewed schemas and implementations.

## Four implemented checks
- Same extracted representation contains terms from two subjects. A topical lead only, not a causal relationship.
- Two different original hashes contain the same literal year-qualified ordinance/resolution/contract/project reference within a conservatively inferred publisher jurisdiction. No joining on personal names. Issuer mapping from publisher URLs is a heuristic; the entity is not independently resolved.
- Byte-identical original content is published at multiple URLs. This is duplication, never independent corroboration.
- The same source URL has different observed original hashes represented in the current text window. This is observed byte variation, not proof of a substantive amendment or its effective date.

## Evidence outputs
public/research-plans.jsonl.gz is the catalog. public/candidates.jsonl holds explicitly unreviewed candidates. public/evidence.jsonl copies the complete selected text representations and locators, not just links, with original SHA-256, extracted-text hash, source URL, page when available and a revision-pinned source link. Original bytes are hash-checked before releasing a candidate; this checks integrity, not factual truth or source independence. OCR accuracy remains unverified. public/run-status.json records actual coverage, plan receipts, errors and counts; reviewed_findings remains zero. No candidates are promoted automatically to investigative findings or allegations.

## Bounded, resumable operation
Configured for deployment, manual invocation and scheduled attempts every six hours at minute 31 UTC. No routine chat interaction is needed. GitHub may delay jobs and network, permission or runner failures can occur; error-free or uninterrupted execution is not guaranteed. The worker rotates a saved plan cursor through up to 512 eligible variants per attempt, a rotating input window of at most 2,000 representations and 12,000,000 text bytes, a 420-second soft analysis budget, and at most 200 candidate rows, with at most five rows per variant. Current published output is capped at 25,000,000 bytes. Failed publication does not advance the committed checkpoint. These are soft operational limits, not proof of exhaustive combinations or complete historical coverage. Some relevant records may never coincide in a window.

## Free-only boundary and storage
Standard ubuntu-latest runner, Python standard library, no paid model/API, subscription, LFS, artifact storage, cache purchase, external service or billing change. Account billing settings are not inspected or modified. The source checkout is temporary and not committed. Only approved derived outputs and engine-state.json are published. Output bounds do not cap accumulated Git history. This separate analysis repository does not fix the source archive's capacity pause or resume its 966 pending government URLs and 546 pending PDFs reported in the previously checked checkpoint. Additional source-data partitioning remains a distinct action.

## Verification before deployment
Local syntax, unique-plan generation, all four algorithm fixture checks and rejection of a cross-issuer identifier match passed. An end-to-end synthetic public-corpus fixture produced 10,080 catalog entries, checked 512 eligible variants, validated source hashes, copied evidence and advanced the checkpoint. Fixture results are not actual county findings. Live execution has not been verified before this deployment.
