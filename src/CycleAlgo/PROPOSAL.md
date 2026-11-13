# Fosol-Cycle: District-Level Crop Rotation Explorer

> **Status:** Proposal for discussion, not a finalized agronomic specification.
>
> **Challenge:** Field Shift: Adapting Farms with NASA Data — NASA Space Apps 2026.
>
> **Initial scope:** Rajshahi, Bangladesh. No farmer questionnaire or technical data entry.

## 1. Proposed solution

Fosol-Cycle will help people explore locally relevant crop-rotation strategies using NASA environmental records and researched agricultural information. Instead of asking farmers to enter planting dates, soil pH, irrigation levels, or numerical priorities, the website will present documented district scenarios and explain their trade-offs.

For the Rajshahi pilot, the core experience will compare:

1. One documented existing rotation as the baseline.
2. One researched alternative with a distinct, evidence-supported benefit.
3. A second researched alternative offering a different trade-off.

The specific rotations must be selected through local research and expert review. They are not established by this proposal.

**The central question changes from “Which crop should this farmer plant next?” to “Which rotation strategies are worth considering here, and under what conditions?”**

The output is district-level decision support, not a personalized field prescription, weather forecast, or guarantee of yield, income, or soil improvement.

## 2. Why this is more than a data dashboard

A dashboard describes conditions. Fosol-Cycle should connect those conditions to agricultural choices:

**NASA observations → seasonal environmental patterns → exposure of researched rotations → trade-offs → practical considerations.**

For example, a historical heat pattern may help explain why a rotation warrants closer review if a documented sensitive crop stage overlaps that period. If stage-specific information is unavailable, the tool must limit its claim to calendar overlap or general exposure rather than predicting crop damage.

Every highlighted benefit or concern should identify its supporting evidence. NASA charts alone do not establish that one rotation is better than another.

## 3. Alignment with the challenge

This proposal is based on the challenge description and video transcript supplied during project discussion. The Resources tab has not yet been reviewed.

| Challenge theme | Proposed response |
|---|---|
| NASA Earth observations | Analyze relevant historical temperature, rainfall, and other available environmental variables. |
| Local agricultural context | Use researched crop profiles, local rotation practices, and suitable soil information. |
| Rotation exploration | Compare a documented baseline with two researched alternatives. |
| Farmer priorities | Show understandable perspectives, such as water conservation or crop diversity, without requiring numerical weights. |
| Explainability | Link conclusions to sources, assumptions, and individual checks. |
| Uncertainty | Show missing evidence, data coverage, geographic limitations, and local review needs. |
| Farmer-centered design | Provide a readable district page without technical data entry. |

The challenge permits several tool formats and does not require a questionnaire, machine learning, or every listed NASA dataset. Comparing three strategies is our proposed demonstration scope, not a claim that the supplied wording makes it mandatory.

## 4. User experience

A user opens the Rajshahi page directly. Future districts may have separate pages or a simple location selector; automatic geolocation is not necessary.

### A. Understand local conditions

Show a small number of relevant seasonal findings in plain language, with their dates, geographic coverage, and sources. Distinguish typical historical conditions from observed changes over time. Do not label a pattern as a trend without an appropriate analysis.

### B. Compare rotation strategies

Present the baseline and alternatives together. Each strategy includes:

- A seasonal timeline showing crops, transitions, and documented fallow periods.
- Calendar compatibility and any tight or unsupported transitions.
- Environmental exposure supported by the available historical data.
- Water-demand information or compatibility conditions, where evidence permits.
- Crop-diversity and legume-related proxies, clearly labeled as proxies.
- Practical prerequisites and unresolved questions.

### C. Understand the trade-offs

Each comparison should answer:

- What changes from the baseline?
- Why is this strategy being considered?
- What evidence supports the potential benefit?
- What may become more difficult?
- What must a farmer or local expert check before adoption?

Lead with readable explanations and timelines. Place detailed charts, definitions, and sources underneath. Do not rely on color alone to communicate status.

## 5. Data and scenario approach

Removing farmer input moves responsibility to the project team. All scenario assumptions must be visible rather than silently treated as facts about every farm.

| Information | Proposed source and handling |
|---|---|
| Existing rotation | Local agricultural publications, extension guidance, or expert-reviewed evidence. Label it as a documented baseline, not universal practice. |
| Alternative rotations | Locally credible sequences selected through research and review, not arbitrary combinations of crops. |
| Crop requirements | Existing crop research dataset, after checking applicability, completeness, and source definitions. |
| Crop durations | Verify whether each duration starts at sowing, transplanting, or another stage. |
| Planting schedules | Documented local ranges, including season and establishment method where relevant. |
| Turnaround time | Reviewed scenario ranges. If unavailable, mark dependent calendar conclusions as unresolved. |
| Environmental history | Start by auditing the existing NASA POWER data for variables, units, missing values, spatial coverage, and complete periods. |
| Local soil context | Suitable local sources at their stated resolution. Do not treat district summaries as field measurements. |
| Water access | Explicit scenario conditions or prerequisites; never infer an individual farm's irrigation access from location alone. |
| Economics and markets | Include only supported information. Otherwise identify the evidence gap rather than assign an income score. |

The existing repository datasets are starting assets, not automatically validated inputs for every proposed comparison.

If materially different water-access conditions must be represented, show separate labeled scenarios. If evidence is missing, retain the uncertainty rather than inventing a district default.

## 6. Decision approach

Use a transparent rule-based comparison first. Machine learning is not necessary for the proposed MVP.

### Step 1: Define comparable scenarios

Choose the district, baseline, alternatives, common analysis period, and comparison horizon. Use one defined annual cropping cycle for the pilot, including transitions across calendar years and the link into the next cycle where relevant.

Document assumptions and ensure the strategies are being compared under compatible conditions.

### Step 2: Validate the evidence

Check crop identifiers, duration reference points, planting windows, units, missing values, source applicability, and climate coverage before calculating results.

Use complete periods appropriate to each historical comparison. Do not treat incomplete records as complete seasonal or annual baselines. Missing observations are not evidence of favorable conditions.

### Step 3: Evaluate every crop transition

Reuse the original calendar logic to estimate harvest and field-ready ranges, then compare each transition with the relevant planting window.

- Preserve ranges instead of replacing them with averages.
- Select the correct seasonal occurrence for each crop.
- Handle cross-year dates explicitly.
- Show waiting and fallow periods rather than automatically treating long waits as practical recommendations.
- Check whether a changed crop conflicts with the following crop, not only whether it can be planted immediately.

Use `SAFE`, `COMPRESSED`, `OUTSIDE_SUPPORTED_WINDOW`, and `UNKNOWN` as calendar statuses. Explain that `SAFE` means calendar fit under stated assumptions, not proven overall suitability.

An unsupported transition keeps a strategy out of the normally supported set unless further evidence resolves it. It does not prove biological impossibility. Missing evidence produces a conditional or insufficient-evidence assessment rather than an automatic pass or failure.

### Step 4: Attach historical environmental evidence

Compare the strategies' seasonal calendars with relevant historical conditions. Where coverage allows, report the frequency of defined exposure indicators across comparable historical seasons, alongside the indicator definition and sample coverage.

Keep these distinctions explicit:

- Historical observations are not future weather forecasts.
- A historical anomaly is not automatically outside a crop's tolerance.
- Regional or gridded observations are not measurements from an individual field.
- General crop tolerances do not establish stage-specific failure thresholds.

### Step 5: Compare agricultural trade-offs

Show separate components rather than immediately compressing them into one score:

| Component | Permitted interpretation |
|---|---|
| Calendar fit | Whether researched crop schedules can connect under stated assumptions. |
| Heat or rainfall exposure | Historical exposure indicators, not predicted yield loss. |
| Water | Sourced crop-demand context or explicit compatibility conditions, not exact irrigation requirements. |
| Rotation diversity | Crop-family and legume proxies, not measured nitrogen balance or soil-carbon change. |
| Soil suitability | Supported compatibility at the available geographic resolution; unresolved where evidence is insufficient. |
| Practical feasibility | Known prerequisites and gaps concerning seed, equipment, labor, irrigation, or markets. |

Only aggregate quantities that are genuinely comparable. Do not add categorical ratings as though they were physical measurements, or infer irrigation demand by subtracting rainfall from generic crop water needs.

### Step 6: Present conditional conclusions

Return a side-by-side comparison with reasons, cautions, and evidence quality. No single overall winner is required for the MVP.

Perspective labels such as “worth considering for crop diversity” may be used only when supported. They must not imply that we know an individual farmer's priorities.

Keep source confidence separate from scenario completeness. A strong crop source cannot compensate for missing local soil information or inadequate climate coverage. If no alternative is sufficiently supported, say so rather than forcing a recommendation.

## 7. Changes from the original PDF

| Original design | Proposed change |
|---|---|
| Farmer questionnaire | Researched district scenarios with visible assumptions. |
| Personalized current-crop assessment | Comparison of documented local practices and alternatives. |
| One next-crop transition | All relevant transitions within the selected rotation cycle. |
| Farmer-entered priority weights | Readable, side-by-side priority perspectives. |
| Ranked replacement crops | Strategy comparisons with conditional conclusions. |
| Climate lookup around a proposed date | Historical seasonal analysis with explicit coverage and limitations. |
| Crop-profile confidence | Separate reporting of source quality, scenario assumptions, and missing evidence. |

Retain the crop research pipeline, generic crop rules, calendar calculations, constraint-first reasoning, and explanation layer where applicable. The original transition evaluator becomes part of the rotation comparison rather than the whole product.

## 8. Focused MVP and implementation order

1. Review the challenge Resources tab and record relevant data guidance.
2. Establish one documented Rajshahi baseline and two credible alternative rotations.
3. Audit the existing crop and NASA datasets against those scenarios.
4. Resolve duration definitions, seasonal dates, and turnaround assumptions.
5. Produce a reproducible comparison for the three strategies, including uncertainties.
6. Review agricultural claims with a suitable local expert and revise unsupported conclusions.
7. Build one district page with a comparison table, seasonal timelines, evidence summaries, and sources.

No backend framework, map library, or new dependency is selected by this proposal. For a fixed district pilot, comparisons may be generated ahead of time and served as data; a live calculation API is only needed if later interaction requires it.

### Out of scope for the initial MVP

- Nationwide recommendations without district-specific evidence.
- Individual field prescriptions or automatic assumptions about farm conditions.
- Live forecasts, exact yield predictions, or guaranteed income estimates.
- Exact soil-health, nitrogen-balance, or irrigation-demand modeling.
- Unvalidated weather-to-harvest-delay formulas.
- Machine learning or multi-satellite fusion added without a concrete analytical need.
- An LLM deciding agronomic feasibility or overriding evidence-backed constraints.

## 9. Validation and success criteria

The MVP succeeds if a user can understand how the baseline and alternatives differ, why those differences matter locally, and what remains uncertain.

Before presenting results:

- Check calendar boundaries, cross-year transitions, duration ranges, and conflicts with the following crop.
- Verify that missing climate or agricultural data cannot produce a favorable assessment by default.
- Trace each material conclusion to a source, reproducible calculation, or explicit assumption.
- Confirm that changing a preference perspective cannot override an established constraint.
- Review whether district-level language could be mistaken for field-specific advice.
- Seek feedback on whether farmers can understand the comparison without interpreting raw scientific charts.

No result should be labeled validated merely because the software runs correctly. Computational checks and agricultural review address different kinds of correctness.

## 10. Decisions still needed

1. Which existing Rajshahi rotation is sufficiently documented to be the baseline?
2. Which two alternatives are locally credible and meaningfully different?
3. Which crop schedules, duration definitions, and turnaround ranges are supported?
4. What soil information and water-access conditions can we represent honestly?
5. Which historical period and environmental indicators have adequate coverage?
6. Who can review the agricultural interpretation before public presentation?

These decisions should drive the analysis and interface—not the other way around.

## Summary

**Remove the technical questionnaire, not the decision-support reasoning.** Fosol-Cycle will use NASA environmental evidence and local agricultural research to explain district-relevant rotation choices, while making assumptions, trade-offs, and limits visible.
