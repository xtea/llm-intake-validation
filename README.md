# llm-intake-validation

Code, prompts and per-meal model outputs for:

> Xiaomeng Li. *Small Average Error, Wide Individual Error: General-Purpose LLMs Estimating Energy Intake from Meal Photos in a Feeding Trial.* Preprint, 2026.

The repository also contains an earlier background experiment (agentic search over estimation pipelines on Nutrition5k), reported in Appendix E of the paper.

## What is here

| Path | Content |
|---|---|
| `FINAL-PLAN.md` | Pre-registration and all addenda, in the order they were written. The commit history is the timestamp record; addendum H is the main study. Post hoc analyses are marked as such. |
| `fe/intake.py` | Builds consumed-intake labels from ACETADA and runs a two-photo candidate (`build`, `run`, `report`). |
| `fe/intake_report.py` | Main analysis (Q1–Q3, macronutrients) → `results/intake.txt`. |
| `fe/intake_extra.py`, `fe/intake_more.py`, `fe/intake_rev.py` | Exploratory analyses added after the main results (effect modification, decomposition, local recalibration, fixed-fraction baseline, sensitivity). |
| `fe/evaluate.py` | Single-photo evaluator with static anti-gaming checks; sealed splits need `--final`. |
| `fe/llm.py` | Cached, cost-counted client for the Anthropic and OpenAI APIs. |
| `fe/figures.py`, `fe/paper_tables.py` | Figures and tables. |
| `candidates/intake/` | Prompts for the before-only, subtraction and both-photos conditions (all six models). |
| `candidates/gen1–3`, `candidates/gpt`, … | Pipelines from the Nutrition5k background experiment. |
| `runs/` | Per-meal outputs of every system, and `runs/cache/` with every model response, keyed by a hash of the request. |
| `results/` | Text outputs of all analyses and the figures. |

## Data (not redistributed)

- **ACETADA** (CC BY-NC 4.0, non-commercial research): https://skynet.ecn.purdue.edu/~coburn6/ACETADA/ — place the release under `data/acetada/ACETADA-release/`.
- **Nutrition5k** (CC BY 4.0): https://github.com/google-research-datasets/Nutrition5k
- **NutritionVerse-Real** (CC BY-NC-SA 4.0): https://www.kaggle.com/datasets/nutritionverse/nutritionverse-real

Images and labels are not included. Use of each dataset must follow its own license.

## Reproduce

Python 3.12; `pip install anthropic==0.84.0 openai==2.28.0 matplotlib==3.11.2 pillow`. macOS `sips` is used for image conversion.

```bash
python3 -m fe.intake build                      # labels + PNG images (needs the ACETADA release)
python3 -m fe.intake_report > results/intake.txt # all main tables, from cached outputs
python3 -m fe.intake_rev                        # exploratory analyses
python3 -m fe.figures results                   # figures
```

Because every model response is cached in `runs/cache/`, the tables and figures can be rebuilt **without any API call** once the labels are built. New calls need `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` (environment or a `.env` file):

```bash
python3 -m fe.intake run candidates/intake/dual_direct_gpt_6_1_sol.py all 20   # last arg: USD cap
```

Hosted models change over time; the cached outputs (called on 16 October 2026) are the reference for the reported numbers.

## License

Code: MIT (see `LICENSE`). Model outputs in `runs/` are provided for research reproducibility.
