# Project guide — Swiss Aargau Lucerne Legal QA

This repository contains the material needed to reproduce the submitted evaluation. Earlier drafting packages, working spreadsheets and pilot notebooks are retained in a separate working archive.

## Reproduce the results

Run `make run` from the repository root to build the Docker image and recompute the final results from stored answers and judgments. The Docker image has been built and run successfully on Windows using Docker Desktop. The Python workflow has also been tested locally.

Alternatively, `make run-local` runs the same evaluation using local Python and saves output files under `track_1b/results/`.

The workflow verifies input hashes and 300 unique answers. It checks the final counts of 126 correct and 174 incorrect and reconstructs the original independent judge–human agreement of 42 out of 57 comparable labels. Reproducing these results requires no API key or GPU and makes no new model requests. Building the Docker image requires access to its Python base image.

## Generate fresh model answers

The optional `src/inference.py` script uses the environment variables `LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY`. Its default model is `swiss-ai/Apertus-v1.5-70B:featherless-ai` through the Hugging Face router. The token is not written to disk. The inference settings are temperature 0 and `max_tokens` 1200.

Fresh inference consumes API credits and is not started by the standard reproduction command. Saved answers are skipped when resuming. New answers require new judgments and do not inherit the submitted labels.

Hosted-model inference may produce different wording even with identical settings. The frozen responses are therefore the basis for deterministic score reproduction. The original inference protocols remain in the separate completion archive. In the original run, ins_003 was retried with 2400 tokens after a truncated answer.

## Evaluation evidence

`docs/evidence/` contains the exact grading inputs, model answers, original judge assessments and separate final adjudications. The `audit/` subdirectory preserves the original human sample labels and the previous agr_003 item so that the revised question can be distinguished from the original sample.

Twenty-six cases were jointly reviewed. The agr_003 question was subsequently clarified, answered again and separately judged. Its fresh answer was finalised as incorrect because it asserted an unsupported ten-year isolation maximum.

The final response collection retains 59 unchanged human sample labels. The original independent random review covered 60 answers. The old human label for agr_003 was not transferred to the new response. These two review scopes must be reported separately.

The public evidence includes the substantive adjudication reasons and unchanged original labels. Verbatim conversational confirmations and conversation timestamps are excluded. The original working records remain in a separate archive.

## Language

Project documentation is written in English for the submission audience. Evaluation prompts, legal questions, reference answers, statutory excerpts and grading content remain in German to preserve the tested language and source wording. English documentation uses Aargau and Lucerne for the two cantons. Names in original legal quotations retain their original language.

## Code and dataset

- [GitHub repository](https://github.com/DanielaFshr/swiss-legal-ag-lu-qa)
- [Hugging Face dataset](https://huggingface.co/datasets/DanielaFshr/swiss-legal-ag-lu-qa)
- [Technical report](../technical_report.md)
- [Dataset licence](../../LICENSES.md)
