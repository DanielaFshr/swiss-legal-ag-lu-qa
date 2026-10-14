# Technical report — Swiss Legal QA

Swiss Legal QA evaluates factual statutory knowledge and short legal reasoning in a Swiss setting. Its 300 German-language questions cover federal law and the cantons of Aargau and Lucerne. The final adjudicated collection contains 126 correct and 174 incorrect answers from Apertus v1.5 70B, giving 42.0% accuracy without retrieval.

**Track:** 1B, Core Task Intelligence. **Event:** Online Hack Apertus 2026. **Project title:** Swiss Legal QA, working title pending final team naming. No demo video is claimed.

## Use of Apertus

Model: swiss-ai/Apertus-v1.5-70B, inference through the Hugging Face router with featherless-ai. The project evaluates outputs rather than fine-tuning model weights. This text-only protocol does not evaluate the multimodal capabilities of Apertus 1.5.

## Use Case Description

Swiss legal questions often require precise distinctions between federal and cantonal law, competent authorities, cumulative conditions and statutory exceptions. Fluent general explanations can sound plausible while changing a decisive requirement. The dataset evaluates these distinctions using short answers grounded in official legislation.

## Dataset Summary

The catalogue contains 300 single-turn Q&A items across 25 topics. There are 169 federal, 62 Aargau and 69 Lucerne questions. All are written in de-CH and include reference answers, answer variations and primary-source citations. A 66-item development cohort is distinguished from 234 expansion items. The topic distribution is purposive rather than representative of the frequency of real legal enquiries.

## Data Collection Method

The curator selected useful provisions from Fedlex and the two cantonal law collections. LLM-assisted drafting produced cases, references and criteria. Stable IDs and metadata link every answer to its legal provision. Package samples were approved by the curator. The original 60-answer random review was selected with seed 20261014 and completed before the disputed-case adjudication. No real client files or recruited research participants were used.

## Dataset Details

Items store their question, reference, variants, jurisdiction, task type, difficulty, expected decision where applicable, required facts, split criteria, scoring policy, legal excerpt and source version. Automated validation checks joins, unique IDs, schema consistency and literal quote evidence. This is not a claim that all 300 references were independently verified by a legal specialist. Official enactments are distinguished from the curated dataset licence.

## Evaluation

### Method

GPT 6 Mittel was used as judge in separate ChatGPT conversations. It assessed criteria and supplied answer quotes. Python rules 0.5 calculate coverage and three-way labels. An 80% threshold is combined with item-specific critical criteria, explicit contradictions and material extra errors. Semantic equivalence is accepted. Scores are coverage, not accuracy probabilities. Cases requiring review retain their original judge record and receive a separate final decision.

### Evaluation setup and inference parameters

The answer instruction was: “Beantworte die folgende Frage nach Schweizer Recht. Antworte kurz und begründe mit den wesentlichen Voraussetzungen.” Temperature was 0 and the normal output limit 1200 tokens. No reference answer, statutory excerpt or retrieval was supplied to Apertus. The original ins_003 answer was truncated and retried with 2400 tokens. All final selected answers ended with stop. Hosted-model inference is not guaranteed to reproduce identical wording. Deterministic score reproduction uses the frozen responses.

### Results

| Collection | n | correct | incorrect | Accuracy |
|---|---:|---:|---:|---:|
| Final catalogue | 300 | 126 | 174 | 42.0% |
| Development cohort | 66 | 18 | 48 | 27.3% |
| Expansion cohort | 234 | 108 | 126 | 46.2% |

The original independent human sample had 60 answers. For 57 comparable initial judge labels, 42 agreed with the original human label, or 73.68%. Three initial judge labels were pending. Original human labels are not overwritten by later consensus. This agreement is not calculated against adjudicated labels.

Twenty-six cases were jointly adjudicated. agr_003 had an under-specified question and was clarified, rerun and judged separately. The fresh answer incorrectly asserted a ten-year isolation maximum. It was manually finalised as incorrect irrespective of unresolved alternative measure categories. The final collection contains 299 original responses and one revised response. Only 59 original independent human sample labels apply unchanged to the final responses. The new answer has a separate final review, not an inherited human label.

## Dataset Limitations

Purposive legal coverage, German only and reuse of pilot cases prevent strong population-level claims. The judge is not API-version pinned. A single human curator and model-assisted adjudication do not provide independent legal ground truth for every judgment. Weights and the threshold are design choices. Compound criteria and additional assertions can affect labels substantially. No systematic contamination analysis was performed. Source versions differ between items and are recorded individually.

## Lessons Learnt and Recommendations

The prototype exposed three recurring issues: a correct outcome with an incorrect legal rationale, additional conditions that narrow a statutory right and criteria that demand more than the question clearly asks. The review therefore distinguishes semantic equivalence from material legal changes. Future work should use clearer atomic prompts, a second independent legal reviewer and a separately reported retrieval-assisted baseline. Prompt or retrieval improvements must not be retroactively attributed to this run.

## Reproducibility

`make run` at the repository root builds a Python Docker image, verifies input hashes and recomputes all labels plus the initial independent agreement. No API keys or GPU are required for this path. The workflow is validated with local Python; Docker verification remains outstanding because Docker is unavailable in the preparation environment. `make run-local` persists outputs under track_1b/results. Fresh inference uses LLM_NAME, LLM_BASE_URL and LLM_API_KEY through src/inference.py and requires new judgments. The code is included rather than relying on private ChatGPT history. The final git commit and public URLs must be recorded after publication.

## License

Code: Apache-2.0. Authored documentation: CC-BY-4.0. Curated dataset: CDLA-Permissive-2.0. Official legal excerpts retain their legal-text status and cited sources. No model weights are redistributed.

## References

- Hack Apertus project template: https://github.com/HackApertus/project-template
- Apertus model: https://huggingface.co/swiss-ai/Apertus-v1.5-70B
- Official legislation: https://www.fedlex.admin.ch/, https://gesetzessammlungen.ag.ch/, https://srl.lu.ch/
- Dataset citations and legal versions: per-item metadata in the companion dataset.

Preparation status: report text complete as a draft. Team naming, public URLs, git commit, Docker validation and the PDF export remain before submission.
