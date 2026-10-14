# Swiss Legal QA

Evaluation of Apertus v1.5 70B on 300 German-language Swiss legal questions covering federal law and the cantons of Aargau and Lucerne. Hack Apertus, Track 1B, Core Task Intelligence.

Final labels: **126 correct, 174 incorrect, 0 not attempted**, accuracy **42.0%**. The final collection contains 299 original answers and one fresh answer after clarification of agr_003. This is a descriptive result for this catalogue and prompt without retrieval.

## Reproduce the results

From this repository root, with Docker and GNU Make installed:

```sh
make run
```

No API key, GPU or network access inside the container is required. The image build requires access to the Python base image. The command verifies frozen input hashes, recomputes the scoring and checks the expected counts. Results are printed inside the container. For persistent local output use `make run-local`, requiring Python 3.10 or later. Outputs appear under `track_1b/results/`.

The Python workflow has been executed successfully. Docker is not available in the preparation environment, so a clean Docker run remains to be verified before submission.

## Documentation

- [Project guide](track_1b/docs/PROJECT.md)
- [Technical report draft](track_1b/technical_report.md)
- [Challenge instructions, unchanged](track_1b/README.md)
- [Licensing](LICENSES.md)

The dataset card and Hugging Face export are supplied separately in the preparation package. Public repository and dataset URLs must be added after publication. The report PDF is not yet included in this preparation version.
