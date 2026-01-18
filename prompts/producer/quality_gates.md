# Quality Gates Reference

## Overview

Each phase transition requires passing specific quality checks. This document defines what must be true before moving to the next phase.

---

## Gate: RESEARCH → STRATEGIZE

### Required Validations

1. **Schema Compliance**
   - `strategic_dossier.json` validates against schema
   - All required fields present
   - Data types correct

2. **Content Minimums**
   - [ ] At least 3 strategic tensions identified
   - [ ] At least 1 opportunity zone identified
   - [ ] At least 5 sources cited
   - [ ] Brand visual markers present (at minimum, primary color)

3. **Quality Checks**
   - [ ] Strategic tensions are specific (not generic)
   - [ ] Evidence is cited for each tension
   - [ ] Company name is correct throughout

### Failure Actions
- If schema fails: Log error, attempt repair
- If content minimums fail: Retry research with more specific queries
- If 3 retries fail: Escalate to manual review

---

## Gate: STRATEGIZE → CREATE

### Required Validations

1. **Brief Count**
   - [ ] Exactly 3 concept briefs generated

2. **Assignment Quality**
   - [ ] Each brief assigned to different tension
   - [ ] Slot IDs are "01", "02", "03"
   - [ ] Slot types match: safe_bet, challenger, moonshot

3. **Risk Profile Spread**
   - [ ] At least 2 different risk levels represented
   - [ ] Ideally: low, medium, high distribution

4. **Platform Focus Spread**
   - [ ] Not all briefs targeting same platform
   - [ ] Platform matches slot type expectations

### Failure Actions
- If count wrong: Regenerate briefs
- If assignments overlap: Reassign tensions
- If spread insufficient: Manually adjust

---

## Gate: CREATE → VISUALIZE

### Required Validations

1. **Concept Count**
   - [ ] Exactly 3 concepts generated

2. **Schema Compliance**
   - [ ] Each concept validates against schema
   - [ ] All required fields present

3. **CMO Test**
   - [ ] Each concept has strategic hook in hook field
   - [ ] Hook is >10 characters (not placeholder)

4. **Episode Completeness**
   - [ ] Each concept has exactly 6 episode concepts

5. **Platform Diversity**
   - [ ] No two concepts have same primary platform

6. **ID Correctness**
   - [ ] Concept IDs are: concept_01, concept_02, concept_03

### Failure Actions
- If count wrong: Regenerate missing concepts
- If schema fails: Log errors, attempt repair
- If CMO test fails: Trigger refinement loop
- If diversity fails: Request platform change on one concept

---

## Gate: VISUALIZE → COMPOSE

### Required Validations

1. **File Count**
   - [ ] 3 PNG files generated in onepagers directory

2. **File Names**
   - [ ] concept_01.png exists
   - [ ] concept_02.png exists
   - [ ] concept_03.png exists

3. **File Integrity**
   - [ ] Each file > 100KB (not blank/error image)
   - [ ] Files are valid PNG format

4. **Spec Completeness**
   - [ ] 3 OnePagerSpec objects generated
   - [ ] Each spec has generation_prompt populated

5. **Prompt Logging**
   - [ ] prompts.md saved with all generation prompts

### Failure Actions
- If files missing: Regenerate failed images
- If size too small: Regenerate (likely generation failure)
- If specs incomplete: Log error, complete manually

---

## Gate: COMPOSE → PACKAGE

### Required Validations

1. **Email Completeness**
   - [ ] pitch_email.md generated
   - [ ] Email > 100 characters

2. **Strategic Content**
   - [ ] Email contains "hypothesis" or equivalent
   - [ ] Email mentions all 3 concepts by name

3. **Company Reference**
   - [ ] Company name appears in email
   - [ ] Subject line is properly formatted

### Failure Actions
- If too short: Regenerate with full template
- If missing elements: Add missing sections
- If company name wrong: Correct throughout

---

## Gate: PACKAGE → DELIVER

### Required Validations

1. **Archive Completeness**
   - [ ] All files copied to archive location
   - [ ] Directory structure correct

2. **Package Index**
   - [ ] package_index.md generated
   - [ ] All file paths in index are valid

3. **Material Availability**
   - [ ] Share link generated (or placeholder ready)

### Failure Actions
- If archive incomplete: Retry copy
- If index broken: Regenerate index
- If link fails: Use fallback delivery method

---

## Retry Policy

Each gate allows up to 3 retry attempts before:
1. Marking phase as FAILED
2. Logging detailed error state
3. Alerting for manual intervention

Retry delays:
- Attempt 1: Immediate
- Attempt 2: 2 second delay
- Attempt 3: 4 second delay

---

## Manual Override

Quality gates can be bypassed with manual approval for:
- Known edge cases
- Partial deliveries
- Testing scenarios

Manual override must be logged with reason.
