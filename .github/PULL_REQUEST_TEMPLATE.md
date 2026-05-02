## Description
Please include a summary of the change and which issue is fixed. Please also include relevant motivation and context.

Fixes # (issue)

## Type of change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] This change requires a documentation update

## How Has This Been Tested?
Please describe the tests that you ran to verify your changes.

- [ ] `pytest tests/unit`
- [ ] `pytest tests/e2e`

## Cross-repo coordination
Complete this section when the PR changes contracts, packaging/version expectations, CI sibling refs, or release sequencing.

- Coordination record: <!-- issue / PR family / release-train note, or N/A -->
- Upstream refs validated:
  - `xrtm-data`: <!-- branch / tag / SHA / PR ref, or N/A -->
  - `xrtm-eval`: <!-- branch / tag / SHA / PR ref, or N/A -->
- Downstream follow-up:
  - `xrtm`: <!-- PR / workflow run / release note, or N/A -->

## Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Coordinated validation, when needed, uses explicit upstream refs rather than same-name branch fallback
- [ ] Post-merge validation or release-train follow-up is documented when downstream repos are affected

---

## Maintainer Triage (for reviewers)
_See [xrtm governance triage docs](https://github.com/xrtm-org/governance/blob/main/policies/triage-matrix.md) for classification guidance._

**Scope**: <!-- Core Schema | Package API | Implementation | Infrastructure | Documentation -->
**Priority**: <!-- Release Blocker | High | Medium | Low -->
**Risk**: <!-- High | Medium | Low -->
**Disposition**: <!-- Accept as-is | Accept with changes | Supersede | Defer | Reject -->

**Review Notes**:
<!-- Brief rationale for disposition. Record full details in governance/policies/pr-disposition-log.md -->
