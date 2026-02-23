# Domain \u0026 Tone Refinement Plan

## 1. Analysis Layer (`src/analysis/gemini_analyzer.py`)

- **Action**: Update `JobAnalysis` schema to include `job_domain`.
- **Prompt Update**: Ask Gemini to classify the job's domain (e.g., "FinTech", "HealthTech", "Trading", "Ecommerce").
- **Logic**: We won't filter here (unless strictly requested), but we pass this `job_domain` to Layer 4.

## 2. Document Layer (`src/documents/generator.py`)

- **Action**: Update the System Prompt.
- **New Instruction**:
  > "Compare the 'Job Domain' with the 'Candidate Industries'.
  > If they do NOT match (e.g., Job is 'Trading', Candidate is 'SaaS'), DO NOT claim experience in that domain.
  > Instead, use a 'Pivot' framing: 'While my background is in [Candidate Industry], my experience in [Skill] is highly transferable to [Job Domain]...'"
- **Few-Shot Example**: Add the user's provided "Good vs Bad" examples to the prompt to ground the model.

## 3. Verification

- **Test**: Re-run generation for the BHFT job (Mocking the input data to avoid re-scraping if easier, or just fully running `main.py`).
