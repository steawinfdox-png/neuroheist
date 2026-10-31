# Your first NeuroLens contribution: a 30-minute lab

This lab is for non-CS and health-science students who want to join open source but find model setup, unfamiliar code, and pull requests intimidating. You can improve the language people see without training a model or knowing neuroscience. The goal is one useful, explained change submitted for review.

Allow 30 minutes **after** Git, Node.js 24, and a GitHub account are ready. A facilitator should prepare a running sample demo beforehand; learners do not need to download the MRI model or Gemma to edit, lint, and build the frontend. Full model setup is in [README.md](README.md).

This is an educational software prototype. Its scenarios are not clinical advice or predictions for an individual patient. Use only the supplied de-identified samples in this lab.

## 0–5 minutes: understand what you may reuse

Read [LICENSE](LICENSE): the project's source code is MIT-licensed, so others can reuse and modify it while retaining the required notice. Open source also welcomes documentation, accessibility, and usability contributions.

Code, models, and data have separate licenses. The MIT license does not relicense downloaded model weights or MRI scans. Read [samples/README.md](samples/README.md) for the sample's source and CC BY-SA attribution; follow the linked model documentation in the README before redistributing weights. Keep `.env`, credentials, downloaded weights, and personal scans out of your contribution.

In your own words, answer: “Why can I share this source-code change, and why must I still check a dataset's license?”

## 5–10 minutes: follow one request through the code

Open these files in your editor; reading is enough. No model changes are needed.

| Step | File | What it does in plain language |
| --- | --- | --- |
| Choose a scan | [ScanUpload.jsx](neuroheist/src/components/ScanUpload.jsx) | Sends a chosen NIfTI file to `/upload`. |
| Receive it | [backend/main.py](backend/main.py) | Accepts the upload and starts segmentation. |
| Find a mask | [backend/inference.py](backend/inference.py), [backend/model.py](backend/model.py) | Run the existing MONAI model and save a tumor mask. A mask labels locations in the scan. |
| Show the result | [BrainViewer.jsx](neuroheist/src/components/BrainViewer.jsx) | Displays the scan and mask together. |
| Request a scenario | [TreatmentPanel.jsx](neuroheist/src/components/TreatmentPanel.jsx) | Sends the selected treatment name to `/simulate` and shows loading text. |
| Find evidence | [backend/research_sources.py](backend/research_sources.py) | Retrieves research through optional Tavily or public PubMed. |
| Interpret evidence locally | [backend/summarizer.py](backend/summarizer.py), [backend/gemini_call.py](backend/gemini_call.py), [backend/local_llm.py](backend/local_llm.py) | Gemma extracts and selects study observations; Python checks the quoted measurements. The historical `gemini_call.py` filename remains, but this path uses local Gemma. |

Explain the difference between **segmentation** (a scan mask) and an **educational scenario** (an illustration based on a study). Neither establishes a patient's diagnosis or future outcome.

## 10–15 minutes: make your own working copy

A **fork** is your GitHub copy of the repository. A **branch** holds one proposed change. A **pull request (PR)** asks the original project's maintainers to review it.

On [the repository](https://github.com/steawinfdox-png/neuroheist), click **Fork** and create your copy. Replace `YOUR_GITHUB_USERNAME` below with your actual account name, then run:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/neuroheist.git
cd neuroheist
git switch -c clarify-educational-loading
npm ci
npm ci --prefix neuroheist
```

The root install provides the viewer dependency; the second install provides the React frontend tools. If setup stalls, ask a facilitator to explain the first error instead of guessing at model or system changes.

## 15–20 minutes: make one useful improvement

First check the file and open PRs: someone may have already completed this exercise. Coordinate with the facilitator so learners do not submit duplicate changes.

In `neuroheist/src/components/TreatmentPanel.jsx`, find the `LOADING_STEPS` entry **“Predicting outcome…”**. Change that entry to **“Preparing educational scenario…”** and save the file. This makes the waiting message match the backend's actual behavior: it illustrates study observations and does not predict an individual patient's outcome. Leave the timer and model settings alone.

This is a learner exercise: the guide does not apply the change for you. If the wording is already fixed, choose one comparable, substantive task:

- Document an actual setup error you reproduced, with its cause and a verified fix.
- Improve one confusing control label after explaining the misunderstanding it causes.
- Report an accessibility problem with keyboard steps, expected behavior, and observed behavior; propose a focused fix if you can verify it.

Agree on the scope with a maintainer. Avoid whitespace-only, rename-only, duplicate, or fabricated model-result changes. Small contributions should help an actual user.

## 20–25 minutes: check and explain your change

From the repository root, run:

```bash
npm --prefix neuroheist run lint
npm --prefix neuroheist run build
git diff -- neuroheist/src/components/TreatmentPanel.jsx
```

Record the results accurately. If a check fails, capture the error and get help; do not claim it passed. The diff should show the intended wording change.

For a visual check, have the facilitator run the backend using the README, then run `VITE_API_BASE_URL=http://127.0.0.1:8000 npm --prefix neuroheist run dev -- --host 127.0.0.1`. Open the printed URL, upload `samples/BRATS_457.nii.gz`, and request a scenario. Observe the loading message if the request lasts long enough; the messages cycle on a timer, not measured backend progress. Capture only the supplied sample, never personal medical data. Record “not observed” if the state passed too quickly.

Explain why this changes communication rather than model accuracy. If no backend is available, report lint/build verification and say the loading state was not visually checked.

## 25–30 minutes: submit a reviewable pull request

Stage only your intended file. This repository may show changes inside tracked dependencies after installation; do not include them in this PR.

```bash
git add neuroheist/src/components/TreatmentPanel.jsx
git diff --cached
git commit -m "Clarify educational scenario loading message"
git push -u origin clarify-educational-loading
```

For a different exercise, substitute its file and a descriptive commit message. On your fork, click **Compare & pull request**, targeting `steawinfdox-png/neuroheist`. Use this description, replacing every bracketed item with truthful evidence:

```text
Problem: [Who misunderstood what, and why it matters.]
Change: [The specific behavior or explanation improved.]
Validation: [Lint/build results; visual steps and screenshot if observed.]
Limits: [Anything not checked; no claim of improved clinical/model accuracy.]
Related issue: [Issue link, if one exists.]
```

Review the staged diff and screenshot for secrets before submission. A PR is a request for review, not a guarantee of a merge or prize. Read feedback, ask when it is unclear, and push corrections to the same branch.

## Reuse this lab in a club or classroom

A facilitator can reuse this openly licensed guide with the source and license notice. Prepare Node/Git, cache dependencies, run the sample backend, and demonstrate a fork before starting the timer. Pair learners who want support. Assign distinct useful issues if the loading-text task is already claimed; one learner may drive while another explains the pipeline.

For a short demo, invite a newcomer outside the project team to explain the two model roles, make a change, and show their PR. Ask where the instructions were unclear. Welcome questions, explain review comments without jargon, and thank people for reproducible reports even when a proposed fix needs revision.

**Measurement plan, not results:** count consenting participants who complete the pipeline explanation, pass their relevant checks, and open a first PR within the session. Record completion time and anonymous points of confusion. Compare completions with starters and revise the lab around the biggest barrier. No newcomer pilot or learning-outcome improvement has been measured yet; report a future pilot honestly, including incomplete attempts.

This learning artifact targets the audience, reuse, contribution, and demonstration goals of [RowdyLaunch's Open Source Education track](https://rowdylaunch.vercel.app/guide). For more help, see GitHub's official [contribution guide](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-open-source) and [fork instructions](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo).
