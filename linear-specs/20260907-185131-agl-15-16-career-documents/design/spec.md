# Feature Specification: Portable Resume and Cover-Letter Plugin

**Feature Branch**: `linear/agl-15-16-career-documents`

**Created**: 2026-09-07

**Status**: Planned — executed by `linear-specs/20260907-185131-agl-15-16-career-documents/plan.md`

**Input**: User description: "AGL-15 — Build a portable resume and cover-letter plugin (https://linear.app/agent-layer/issue/AGL-15/build-a-portable-resume-and-cover-letter-plugin). Create a standalone open-source `career-documents` plugin that works without agent-layer; agent-layer may install it. Keep one provider-neutral workflow source with thin packages for ChatGPT/Codex and Claude Code/Cowork. Model four authorities separately: qualifications, voice, document templates, and target role. Personal data and personal templates stay outside the public repository. Optional `career-documents.json` only locates providers, templates, outputs, and workflow policy; it stores no qualifications or credentials. Use a versioned `CareerProfile` model with stable IDs, provenance, verification state, dates, visibility, and conflict rules. Structured Markdown is the reference provider; Basic Memory is the first MCP provider. All authoritative updates are proposed as reviewable diffs. Implement four interactive flows: onboard/import; update qualifications; map a job description to evidence and generate a tailored resume; generate a complementary cover letter. Requirement mapping classifies evidence as direct, transferable, or a gap and supports executive and builder positioning through selection and emphasis. MVP uses existing file, MCP, and document tools. A hosted service, custom UI, and submitting applications are outside scope."

## Clarifications

### Session 2026-09-07

- Q: Which open-source license does the public repository ship? → A: MIT.
- Q: When both a structured-Markdown location and a Basic Memory project are configured, which one is authoritative? → A: The workspace configuration names exactly one authoritative provider; structured Markdown is the default when nothing is configured, and Basic Memory can be named authoritative with structured Markdown as the derived export.
- Q: What format are applicant-owned document templates? → A: An editable word-processing document (DOCX) with a sidecar manifest that names its placeholders, sections, and page budget; the shipped sanitized example template is the reference.
- Q: How are PDFs produced when the agent platform has no converter? → A: A local headless converter is used when present; otherwise the flow uses the platform's own document tools to export, and the checks run on whichever PDF results. A missing converter is reported, never silently skipped.
- Q: How many positioning modes exist in the MVP? → A: Exactly two named modes, executive and builder, chosen per document; the role brief recommends one and the applicant can override it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the plugin and see the same flows everywhere (Priority: P1)

An applicant installs career-documents from the public repository onto Claude Code (or Cowork) or onto Codex (or ChatGPT), follows the setup document for that platform, and finds the same four flows available with the same names, descriptions, and behavior. Nothing about the applicant is stored inside the plugin.

**Why this priority**: Every other story depends on the plugin being installable, and the portability promise (one source, two thin packages) is the ticket's first acceptance criterion.

**Independent Test**: Install each package on a machine profile with no prior configuration, list the available skills, and compare the inventories: the four flow skills are present on both with identical names, descriptions, and versions, and the plugin install directory contains no applicant data.

**Acceptance Scenarios**:

1. **Given** a machine with Claude Code and no career-documents install, **When** the applicant follows the Claude setup document, **Then** the four flow skills are listed and each can be invoked by name.
2. **Given** a machine with Codex and no career-documents install, **When** the applicant follows the Codex setup document, **Then** the same four flow skills are listed with the same names and descriptions as the Claude package.
3. **Given** both packages built from the same commit, **When** their skill inventories are compared, **Then** there are zero differences in skill names, descriptions, or versions.
4. **Given** the public repository at any commit, **When** the applicant-data guard runs, **Then** it reports zero personal-data patterns outside the sanitized example and fixture folders.

---

### User Story 2 - Onboard existing material into one authoritative profile (Priority: P1)

An applicant with existing résumés, a professional-network export, brand or voice notes, and scattered facts runs the onboarding flow. The flow inventories the sources, extracts candidate facts with their provenance, merges duplicates, asks only the questions whose answers change a fact (conflicts, missing dates, visibility), and proposes a single reviewable diff to the chosen authoritative provider. On approval the profile is written once; every other copy is marked derived. The flow can be interrupted and resumed without re-asking anything already answered.

**Why this priority**: Every document the plugin produces is only as trustworthy as the profile it draws from; onboarding is what creates the single authority the constitution demands.

**Independent Test**: Run the onboarding flow against the sanitized example sources (two résumés that disagree on one date, one network export, one voice note), answer the conflict question, approve the diff, and confirm the provider holds one profile whose facts each carry an ID, provenance, verification state, dates, and visibility, with the conflict recorded and resolved.

**Acceptance Scenarios**:

1. **Given** two source documents that state different end dates for the same role, **When** the flow extracts facts, **Then** it records one role with both provenance entries and asks exactly one question to resolve the date.
2. **Given** the applicant answers the conflict question and approves the proposed diff, **When** the diff is applied, **Then** the authoritative provider contains exactly one entry for that role with the chosen date, both provenance entries, and a verification state of applicant-verified.
3. **Given** the flow is interrupted after questions were answered but before approval, **When** it is resumed in a later session, **Then** it continues from the pending diff without repeating any answered question.
4. **Given** a fact the applicant marks private, **When** the profile is written and later exported, **Then** the fact is present in the authoritative profile and absent from every generated document.
5. **Given** the authoritative provider is Basic Memory, **When** the diff is applied, **Then** the same facts are written as notes with the same IDs, and the structured-Markdown export is produced and labeled derived.

---

### User Story 3 - Generate a tailored résumé for a job description (Priority: P2)

An applicant provides a job description. The flow produces a role brief (organization, role, seniority, must-have and nice-to-have requirements, keywords, recommended positioning), then a requirement-to-evidence map that classifies each requirement as direct, transferable, or a gap and cites the profile IDs behind every claim, then a content plan that selects and orders profile entities and sets emphasis for the chosen positioning (executive or builder) within the template's page budget, then renders the résumé into the applicant's approved template in the applicant's approved voice. The output passes the checks and is recorded with its source IDs, role brief, template, voice profile, and plugin version. The flow never adds a qualification the profile does not contain.

**Why this priority**: The tailored résumé is the plugin's primary value; it is the first story that turns the profile into something the applicant sends.

**Independent Test**: Run the flow with the sanitized example profile and an example job description that contains one requirement the profile does not meet; confirm the map marks it as a gap, the résumé contains no claim for it, every claim in the rendered document traces to a profile ID, the document fits the page budget, and the output record lists every source ID.

**Acceptance Scenarios**:

1. **Given** a job description and an approved profile, **When** the flow runs, **Then** it produces a role brief, a requirement-to-evidence map, a content plan, and a rendered résumé, in that order, each saved in the application's output folder.
2. **Given** a requirement with no supporting evidence, **When** the map is built, **Then** the requirement is classified as a gap and no sentence in the rendered résumé claims it.
3. **Given** the applicant selects builder positioning, **When** the content plan is built, **Then** hands-on entities are selected and emphasized ahead of leadership entities, and switching to executive positioning inverts that emphasis without changing any fact.
4. **Given** the rendered résumé, **When** the checks run, **Then** factual traceability, link and date validity, text extraction, pagination, and rendered-layout inspection each pass, and the output record stores the results.
5. **Given** selected content exceeds the template's page budget, **When** the content plan is finalized, **Then** lower-emphasis entities are cut, the cut list is reported to the applicant, and no fact is shortened by inventing a different fact.

---

### User Story 4 - Generate a complementary cover letter (Priority: P3)

Using the same role brief and requirement-to-evidence map, the applicant asks for a cover letter. The flow drafts a letter in the applicant's voice that complements the résumé rather than repeating it, addresses the highest-value requirements with cited evidence, handles gaps honestly or omits them, fits the letter template's page budget, passes the checks, and is recorded like the résumé.

**Why this priority**: A letter is expected alongside most applications, and it reuses the résumé flow's artifacts, so it is cheap once the résumé story exists.

**Independent Test**: With the example role brief, map, and résumé from the résumé story, generate the letter and confirm every claim traces to a profile ID, the letter does not restate the résumé's bullet points verbatim, gap requirements are not claimed, and the checks and output record are produced.

**Acceptance Scenarios**:

1. **Given** an existing role brief and map for a role, **When** the applicant requests a cover letter, **Then** the flow reuses them without re-asking questions already answered for the résumé.
2. **Given** the letter is rendered, **When** the checks run, **Then** every claim traces to a profile ID, no gap requirement is claimed, and the letter fits its page budget.
3. **Given** the résumé for the same role, **When** the letter's sentences are compared against the résumé's bullets, **Then** no bullet is reproduced verbatim.

---

### User Story 5 - Update qualifications after onboarding (Priority: P3)

The applicant adds a new role, achievement, credential, or correction. The flow captures the change with its provenance, proposes a reviewable diff to the authoritative profile, applies it on approval, refreshes derived exports, and reports which previously generated documents reference changed facts and are now stale.

**Why this priority**: Profiles change continuously; without this flow the applicant would edit the authority by hand and lose provenance and verification state.

**Independent Test**: Apply an update that changes one fact's end date in the example profile, approve it, and confirm the authoritative profile and the derived export both reflect it and the previously generated example résumé is listed as stale.

**Acceptance Scenarios**:

1. **Given** an applicant describes a new achievement, **When** the flow proposes the diff, **Then** the new fact carries a fresh stable ID, provenance naming the applicant's statement, and a verification state of applicant-verified.
2. **Given** the diff is approved, **When** it is applied, **Then** the authoritative provider and every derived export agree, and each output record whose source IDs include a changed fact is reported stale.
3. **Given** the flow is interrupted before approval, **When** it resumes, **Then** the pending diff is shown again without re-asking anything.

---

### Edge Cases

- Two sources disagree on the same fact: both provenance entries are kept, one conflict is recorded, one question is asked, and the fact is unusable in documents until resolved.
- A job description requirement has no evidence: it is a gap, never a claim; the cover letter may address it honestly or omit it.
- Selected content does not fit the page budget: the content plan trims by emphasis rank and reports the cuts; it never rewrites a fact into a smaller fact.
- The authoritative provider is unreachable (for example the Basic Memory connection is down): flows run read-only against the last derived export, label every result derived, and refuse writes.
- A flow is interrupted: it resumes from persisted state and never repeats an answered question.
- Applicant data appears inside the repository or plugin install path: the guard fails the gate and the flow refuses to write there.
- A fact is marked private: it never appears in output; a fact marked restricted appears only after per-document approval.
- A template placeholder has no matching content: the placeholder is removed cleanly and reported, never left visible.
- Dates or links in a source cannot be validated (a future date, a dead link): the check fails and names the item.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST live in a standalone public repository containing the shared flow skills, the Claude Code/Cowork package, the ChatGPT/Codex package, sanitized examples and templates, setup documents for each platform, an MIT license, and no applicant data.
- **FR-002**: The repository MUST include an automated guard that fails when personal-data patterns (email addresses, telephone numbers, postal addresses, or non-example person names) appear outside the sanitized example and fixture folders.
- **FR-003**: Workflow logic MUST exist once, as provider-neutral skills; each platform package MUST expose the same skill inventory (names, descriptions, versions) and MUST NOT contain flow logic of its own.
- **FR-004**: The plugin MUST work with no configuration file, using documented defaults, and MUST honor an optional `career-documents.json` that locates the authoritative provider, additional providers, templates, voice profile, output folders, and workflow policy, and MUST reject a configuration that contains qualifications or credentials.
- **FR-005**: The plugin MUST define a versioned `CareerProfile` schema in which every fact carries a stable ID, provenance (source, extraction method, date), verification state, start and end dates where applicable, visibility, and any recorded conflicts.
- **FR-006**: The plugin MUST define a provider contract covering read, propose-diff, apply-approved-diff, and export, with documented precedence and deduplication rules, and MUST implement it for structured Markdown (the reference provider) and for Basic Memory (the first MCP provider).
- **FR-007**: Exactly one provider MUST be authoritative at a time; every other copy MUST be labeled derived, and the plugin MUST never let a derived copy overwrite the authority.
- **FR-008**: Every change to the authoritative profile MUST be presented as a reviewable diff and applied only after the applicant approves it, with the approval recorded.
- **FR-009**: The onboarding flow MUST inventory the applicant's sources, extract candidate facts with provenance, merge duplicates, surface conflicts, and produce one proposed diff.
- **FR-010**: Each flow MUST persist its state so that an interrupted flow resumes without repeating any answered question, and MUST ask a question only when the answer changes a fact's value, visibility, or verification state, or changes what a document contains.
- **FR-011**: The résumé flow MUST produce a role brief containing organization, role, seniority, must-have and nice-to-have requirements, keywords, and a recommended positioning.
- **FR-012**: The résumé flow MUST produce a requirement-to-evidence map that classifies each requirement as direct, transferable, or gap and cites the profile IDs for every claim.
- **FR-013**: The résumé flow MUST produce a content plan that selects, orders, and emphasizes profile entities for the chosen positioning (executive or builder) within the template's page budget, and MUST report anything cut for space.
- **FR-014**: Document generation MUST render into the applicant's approved template and voice profile, both applicant-owned and stored outside the repository, and MUST NOT introduce any qualification, date, employer, title, or metric absent from the profile.
- **FR-015**: The cover-letter flow MUST reuse the role brief and map, produce a letter that complements rather than repeats the résumé, and handle gaps honestly or omit them.
- **FR-016**: Every generated document MUST pass checks for factual traceability (each claim maps to profile IDs), link and date validity, text extraction, pagination within the template's page budget, and rendered-layout inspection before it is presented as complete.
- **FR-017**: Every generated document MUST be accompanied by an output record naming its source IDs, role brief, template, voice profile, positioning, check results, and plugin version.
- **FR-018**: The update flow MUST capture new or corrected facts with provenance, propose a diff, refresh derived exports on approval, and report which earlier outputs reference changed facts.
- **FR-019**: Facts marked private MUST never appear in generated documents; facts marked restricted MUST require explicit approval per document.
- **FR-020**: The repository MUST ship a sanitized, fictional example applicant (profile, sources, voice profile, template, configuration) that exercises every flow and is the fixture for the automated checks.

### Key Entities *(include if feature involves data)*

- **CareerProfile**: The versioned collection of an applicant's facts; has a schema version, the authoritative provider reference, and a set of ProfileEntities.
- **ProfileEntity**: One fact of a given type (contact, experience, education, skill, project, credential, patent, publication, achievement) with a stable ID, dates, visibility, verification state, provenance entries, and any conflicts.
- **Provenance**: Where a fact came from: source reference, extraction method, timestamp, and the actor that recorded it.
- **Conflict**: Two or more candidate values for one attribute of one entity, each with provenance, plus the resolution once chosen.
- **VoiceProfile**: Applicant-owned rules for tone, vocabulary, sentence shape, and forbidden phrasing, with examples.
- **DocumentTemplate**: An applicant-owned editable document plus a manifest naming its placeholders, sections, and page budget.
- **RoleBrief**: The structured reading of one job description, including requirements, keywords, seniority, and recommended positioning.
- **RequirementEvidenceMap**: For one role brief, each requirement's classification (direct, transferable, gap) and the cited profile IDs.
- **ContentPlan**: The selected, ordered, emphasized entities for one document under one positioning and page budget, with the cut list.
- **OutputRecord**: The provenance of one generated document: source IDs, role brief, template, voice profile, positioning, check results, plugin version, and staleness.
- **WorkflowState**: The persisted progress of one flow run: answered questions, pending diff, and the artifacts produced so far.
- **WorkspaceConfiguration**: The optional `career-documents.json`: provider locations, template and voice locations, output folders, and workflow policy; never facts or credentials.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The two platform packages built from one commit expose identical skill inventories: zero differences in skill names, descriptions, or versions.
- **SC-002**: The applicant-data guard reports zero findings outside the example and fixture folders on every commit of the public repository.
- **SC-003**: For the shipped example applicant, every claim in every generated document traces to at least one profile ID: zero untraced claims reported by the checks.
- **SC-004**: For the shipped example applicant, the résumé and cover-letter flows produce documents that pass all five checks without manual editing.
- **SC-005**: Every question a flow asks corresponds to a recorded decision, and resuming an interrupted flow repeats zero previously answered questions.
- **SC-006**: After an approved profile update, the authoritative profile and every derived export agree, and every earlier output whose source IDs changed is reported stale.
- **SC-007**: An applicant following either platform's setup document reaches a working install without steps outside that document.

## Assumptions

- One applicant per workspace; the flows run inside an agent session (Claude Code, Cowork, Codex, or ChatGPT) that has file access to that workspace.
- Basic Memory is reachable as an MCP server when it is the chosen provider; when it is not reachable, flows fall back to read-only use of the derived export.
- Applicant-owned templates are editable word-processing documents with a sidecar manifest; the shipped example template is the reference layout.
- PDFs come from a local headless converter when one is installed, otherwise from the agent platform's document tools; the checks run on whichever PDF results.
- Default page budgets are two pages for a résumé and one page for a cover letter, overridable per template.
- Documents are produced in English in the MVP.
- Out of scope: a hosted service, a custom user interface, submitting applications, multiple applicants per workspace, and guarantees about third-party applicant-tracking-system parsing.
