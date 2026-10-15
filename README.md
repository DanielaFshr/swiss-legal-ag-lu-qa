# Swiss Aargau Lucerne Legal QA

Evaluation of Apertus v1.5 70B on 300 German-language Swiss legal questions covering federal law and the cantons of Aargau and Lucerne. Hack Apertus, Track 1B, Core Task Intelligence.

Final labels: **126 correct, 174 incorrect, 0 not attempted**, accuracy **42.0%**. The final collection contains 299 original answers and one fresh answer after clarification of agr_003. This is a descriptive result for this catalogue and prompt without retrieval.

## Reproduce the results

From this repository root, with Docker and GNU Make installed:

```sh
make run
```

No API key, GPU or network access inside the container is required. The image build requires access to the Python base image. The command verifies frozen input hashes, recomputes the scoring and checks the expected counts. Results are printed inside the container. For persistent local output use `make run-local`, requiring Python 3.10 or later. Outputs appear under `track_1b/results/`.

The Python workflow has been executed successfully. The Docker image has also been built and run successfully on Windows using Docker Desktop.

## Documentation

- [Project guide](track_1b/docs/PROJECT.md)
- [Technical report (Markdown)](track_1b/technical_report.md)
- [Technical report (PDF)](track_1b/SwissLegalTurtle_Report.pdf)
- [Challenge instructions, unchanged](track_1b/README.md)
- [Licensing](LICENSES.md)

## Code and dataset

- [GitHub repository](https://github.com/DanielaFshr/swiss-legal-ag-lu-qa)
- [Hugging Face dataset and dataset card](https://huggingface.co/datasets/DanielaFshr/swiss-legal-ag-lu-qa)

