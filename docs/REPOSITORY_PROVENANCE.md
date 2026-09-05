# Repository Provenance & Git Metadata Audit

**Project:** AdaptiveAI Finance Controller  
**Upstream Foundation:** Securo (`https://github.com/securo-finance/securo`)  
**Repository:** `https://github.com/P-mohith230/Adaptive-AI-final`  
**Date:** September 2026  
**Auditor:** Senior Git/GitHub Engineer & Open-Source Compliance Specialist

---

## 1. Executive Summary

This document provides a formal, evidence-based audit of the Git provenance, remote configuration, commit history, and GitHub contributor attribution for the **AdaptiveAI Finance Controller** repository.

The repository was initially cloned and adapted from the open-source **Securo** project (`https://github.com/securo-finance/securo`), an AGPL-3.0 self-hosted personal finance manager. It is being developed into **AdaptiveAI Finance Controller**, an autonomous financial reconciliation, exception intelligence, and merchant finance operations platform built for the **Razorpay AI Buildathon Track 04**.

A primary concern investigated during this audit is why the GitHub repository interface displays **77 contributors** associated with the upstream Securo project, despite current repository code reflecting the AdaptiveAI project.

---

## 2. Git Provenance Audit Findings

### 2.1 Remote Configuration
Inspection of `git remote -v` and `.git/config`:
```text
origin  https://github.com/P-mohith230/Adaptive-AI-Finance.git (fetch)
origin  https://github.com/P-mohith230/Adaptive-AI-Finance.git (push)
```
- **Current Origin:** `https://github.com/P-mohith230/Adaptive-AI-Finance.git`
- **Upstream Remote:** Not configured in local git (`git config --get remote.upstream.url` returned empty; earlier direct upstream remote was removed).
- **Active Branch:** `main` tracking `origin/main`.

### 2.2 Branch & Commit Structure on `main`
Inspection of `git log --oneline --decorate -20`:
```text
7f1d30a (HEAD -> main, origin/main) feat: AdaptiveAI Finance Controller - AI-Powered Merchant Financial Control & Reconciliation Platform
```
Inspection of commit parents via `git rev-list --parents -n 1 7f1d30a`:
```text
7f1d30aaf08784e992fcb7a8fd70cc6fa40cad6b
```
- The current `main` branch consists of a single root commit (`7f1d30a`) authored by `Mohith Pagadala <pagadalamohith85@gmail.com>`.
- `7f1d30a` has **zero parent commits**, meaning the linear history on `main` was initiated as an independent root tree.
- Inspection of `git ls-remote --heads origin`:
  - `refs/heads/main` -> `7f1d30aaf08784e992fcb7a8fd70cc6fa40cad6b`

### 2.3 Local Tag & Ref Inspection
Running `git for-each-ref` and `git shortlog -sne --all` revealed:
- **Local Tag References:** 76 release tags exist in `.git/refs/tags/` (from `v0.0.1` to `v0.15.0`).
- These tags point to historical commits authored by 77 upstream contributors who built Securo between 2024 and 2026.
- Running `git ls-remote --tags origin`:
  - Output was **empty**. **None of these 76 upstream tags were pushed to the GitHub remote `origin`**. They exist exclusively in the local clone.

---

## 3. Why GitHub Shows Securo Contributors (Root Cause Analysis)

There is a common misconception that editing `README.md`, removing contributor tables, or changing repository descriptions alters the "Contributors" list on GitHub. **It does not.** GitHub's contributor statistics are generated programmatically by backend infrastructure.

The appearance of Securo contributors on `https://github.com/P-mohith230/Adaptive-AI-Finance` is caused by three distinct technical factors:

### Factor A: GitHub Fork Network Linkage
When a repository is created on GitHub using the **"Fork"** button:
1. GitHub registers the repository as a member of the upstream repository's **Fork Network**.
2. GitHub's internal graph database links repository metadata to `securo-finance/securo`.
3. In a fork network, GitHub shares the underlying Git object storage pool across forks. Under the repository header, GitHub displays `"forked from securo-finance/securo"`.
4. The GitHub web UI often associates network-wide contributor metrics or default branch histories with the upstream parent until explicitly detached by GitHub Support.

### Factor B: GitHub Contributor Graph Caching
GitHub's Contributor graph (`/graphs/contributors`) and sidebar widget are calculated asynchronously:
1. When a repository is first created or forked, GitHub indexes all commits on the default branch.
2. If the repository was initially pushed with upstream commits before `main` was re-initialized with commit `7f1d30a`, GitHub's backend caches the contributor metrics.
3. GitHub caches contributor data aggressively; cache invalidation may take 24 to 48 hours following a force-push, or may require a new default branch trigger.

### Factor C: Local vs. Remote Git Objects
While local `git shortlog -sne --all` enumerates all 77 authors because of local refs in `.git/refs/tags/*`, the remote repository on GitHub only has `refs/heads/main`. Therefore, remote contributor attribution is strictly a function of GitHub's fork linkage and commit cache, **not** ongoing live commits from upstream.

---

## 4. Analysis of Git History Strategies

We evaluated three potential Git history management strategies:

| Strategy | Description | Technical Cleanliness | Legal & Attribution Compliance | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A: Full Upstream History Preservation** | Retain all ~2,000 Securo commits in `main` and append AdaptiveAI commits on top. | Preserves full Git blame for every upstream line; larger clone size (~150MB+). | Excellent. Complete commit history remains intact. | Viable, but conflates commit timeline of personal finance with Buildathon submission. |
| **Option B: Clean Project History with Documented Provenance (Current)** | Maintain `main` starting from our derivative release commit, with comprehensive `/docs/OPEN_SOURCE_ATTRIBUTION.md`, `/docs/REPOSITORY_PROVENANCE.md`, and `AUTHORS.md`. | Cleanest for evaluation; clear diff of Buildathon work; fast clone time. | Fully compliant with AGPL-3.0 Section 5 (conveying modified works with prominent notices and license preservation). | **RECOMMENDED** |
| **Option C: Dual-Branch Model** | Keep `upstream/master` (or `vendor/securo-v0.15.0`) containing exact Securo history, and develop on `main`. | Clean separation between upstream base and derivative work. | Very clear technical and legal separation. | Strong alternative if evaluator requests complete Git blame. |

### Why Option B is Recommended
Option B offers the ideal balance for the Razorpay AI Buildathon:
1. **Clarity for Evaluators:** Judges can clearly review our codebase and commits without navigating thousands of historical personal-finance pull requests from 2024.
2. **Strict Legal Compliance:** AGPL-3.0 does not require preserving Git commit hashes; it requires:
   - Conveying modified source code under AGPL-3.0.
   - Prominent notices stating that the files are modified.
   - Preserving copyright notices and upstream license grants.
   - Giving all recipients access to the corresponding source.
   All of these obligations are fully met through our `/docs/OPEN_SOURCE_ATTRIBUTION.md`, `LICENSE`, and file-level notices.
3. **No Authorship Falsification:** We do not claim to have written the upstream code. We explicitly document Securo's authors, upstream repository URL, and license terms.

---

## 5. Handling GitHub Contributor Attribution

To address the display of 77 contributors on GitHub without engaging in misleading practices:

1. **Document the Fork & Provenance (Completed):**
   - Create `docs/REPOSITORY_PROVENANCE.md` (this file) and `docs/OPEN_SOURCE_ATTRIBUTION.md`.
   - Explicitly celebrate and attribute Securo's 77 contributors in `AUTHORS.md`.

2. **If Fork Detachment is Desired (Optional Step for Repository Owner):**
   - If the repository was created using GitHub's "Fork" button and you wish to remove the `"forked from securo-finance/securo"` label and unlink the contributor graph:
     - Contact [GitHub Support](https://support.github.com/contact) with the subject: *"Please detach fork P-mohith230/Adaptive-AI-Finance from securo-finance/securo"*.
     - GitHub Support routinely processes detachment requests for substantial derivative/redirection projects.
   - Alternatively, if a standalone repository is preferred, push `main` to a freshly created (non-forked) empty GitHub repository.
   - Note: Detaching the fork is purely a GitHub UI preference; it has no bearing on software functionality or AGPL-3.0 legal compliance.

---

## 6. Exact Git Verification Commands

To verify local repository state at any time:
```bash
# Verify remotes
git remote -v

# Verify branch commit history
git log --oneline -5

# Verify remote heads on GitHub
git ls-remote --heads origin

# Verify remote tags on GitHub
git ls-remote --tags origin

# Inspect commit author of HEAD
git log -1 --format=fuller
```
