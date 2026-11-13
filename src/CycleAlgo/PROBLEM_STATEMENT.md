# NASA Space Apps 2026 — Problem Statement

## Field Shift: Adapting Farms with NASA Data

> **Document basis:** The challenge description, background, objectives, potential
> considerations, and video transcript supplied by the project team in this
> session. This is a structured restatement, not a verbatim official publication.
> The live challenge page and Resources tab have not been independently checked
> for subsequent updates while preparing this file.
>
> **Official challenge page:**
> https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
>
> This document describes NASA's challenge, not the team's proposed architecture.
> Rajshahi, Python, React, static JSON delivery, and the removal of a farmer
> questionnaire are Fosol-Cycle design choices—not NASA requirements.

## 1. Core challenge

Farmers face shifting temperatures, changing rainfall patterns, water shortages,
extreme weather, and declining soil health. These pressures make it difficult to
choose crop rotations that protect fields, conserve water, and support long-term
resilience.

**Create a decision-support tool that uses NASA Earth observations, together with
local soil information, crop characteristics, and farmer priorities, to help
farmers explore rotation strategies that could strengthen soil health and adapt
their farms to changing conditions.**

The tool should reveal patterns, possibilities, trade-offs, and uncertainty. It
should support—not replace—farmer judgment and local agricultural expertise.

## 2. Background: why the problem matters

Agricultural decisions are becoming more complex as temperatures shift, rainfall
becomes less predictable, and soil health declines. Water shortages, erosion,
nutrient depletion, and extreme weather add uncertainty.

A crop that benefits a rotation in one place may be inappropriate elsewhere. It
may:

- Consume too much water.
- Introduce disease concerns.
- Conflict with local markets.
- Fall outside the expected growing season.
- Offer soil-health benefits that do not outweigh other local constraints.

The challenge is inspired in part by multigenerational farming experience:
families have lived through seasons in which better tools for tracking changing
conditions could have helped them identify healthier and more resilient choices.

NASA's long-term environmental datasets offer ways to understand local growing
conditions. The brief also identifies **SI techniques** as an opportunity to
translate data into practical, farmer-friendly insights. The supplied text uses
the abbreviation “SI”; this document retains it without assigning an unprovided
expansion.

## 3. Objectives and acceptable forms

Teams may combine NASA Earth observations with local agricultural information to
create an:

- App.
- Model.
- Interactive map.
- Visualization.
- Other decision-support tool or a novel format that addresses the challenge.

The goal is to help farmers explore crop-rotation options that **may improve soil
health and strengthen resilience to changing weather and water conditions**.

The tool may identify:

- Periods when fields are typically bare.
- Seasons when current crops appear more vulnerable.
- Opportunities to interrupt pest cycles.
- Options that may reduce water demand.
- Opportunities to improve infiltration.
- Possibilities for supplemental income.

### Strategy comparison

The brief suggests comparing **at least three rotation strategies, including the
existing rotation**. For each strategy, teams may explain:

1. Why it was suggested.
2. What evidence supports it.
3. What benefits it may offer.
4. Where information gaps exist.
5. What risks require review by farmers or local agricultural experts.

The supplied wording is “may compare,” so this is presented here as suggested
scope rather than an explicitly mandatory strategy count.

## 4. NASA datasets identified in the brief

The challenge lists the following datasets or missions as possibilities:

| Dataset or mission | Context suggested by the brief |
|---|---|
| SMAP | Soil-moisture conditions and related patterns. |
| ECOSTRESS | Thermal and evapotranspiration-related context. |
| GPM | Precipitation patterns and events. |
| Landsat | Land-surface and vegetation observations. |
| MODIS | Vegetation and other environmental observations. |
| NASA POWER | Meteorological and related environmental time series. |
| GRACE and GRACE-FO | Long-term water-storage trends. |
| SRTM or other NASA elevation products | Elevation and terrain context. |
| GEDI | Biomass information, mentioned in the optional data-fusion discussion. |

These are possibilities, not a requirement to use every dataset. Specific
products, variables, coverage, and appropriate interpretations must be checked
against their documentation.

### Environmental patterns teams may analyze

- Temperature and heat stress.
- Rainfall patterns and extreme precipitation.
- Soil moisture.
- Evaporation and evapotranspiration-related conditions.
- Frost risk.
- Vegetation stress.
- Long-term water trends.

### Local agricultural information teams may combine with observations

- Local soil information.
- Crop characteristics and growing requirements.
- Farmer priorities and constraints.
- Water use.
- Forage value.
- Nitrogen-fixing potential.
- Erosion reduction.
- Organic-matter improvement.
- Market suitability.

## 5. Potential considerations

**The brief explicitly presents the following as considerations that teams may,
but are not required to, address. They are not a mandatory feature checklist.**

### 5.1 Understanding conditions and data

Teams may explore how temperature, soil moisture, rainfall, evaporation, and
vegetation stress relate to crop vulnerability and soil health.

They may explain scientific concepts such as:

- Evapotranspiration.
- Soil-moisture anomalies.
- Vegetation indices, including NDVI.
- Frost risk.
- Water-balance indicators.

The brief encourages clarifying the differences between satellite observations
and ground-based measurements, including how combining them may improve
accuracy.

### 5.2 SI, modeling, and data fusion

Teams may:

- Compare SI or statistical approaches for detecting patterns in historical
  climate and soil conditions.
- Identify seasonal transitions, bare-field periods, or times when current crops
  show increased stress.
- Explain how the model interprets uncertainty.
- Identify where local expertise is needed to validate results.

When combining datasets with different spatial and temporal resolutions, teams
may harmonize them through downsampling, aggregation, or resampling to a common
analysis grid.

The brief gives examples of combining SMAP soil moisture, ECOSTRESS land-surface
temperature, GPM precipitation, Landsat/MODIS vegetation indices, GEDI biomass,
and soil datasets into coherent features for explainable strategy comparisons.

This is a possible analytical approach, not an instruction to implement all of
those data sources or processing methods.

### 5.3 Rotation-strategy exploration

Teams may compare strategies through:

- Nutrient cycling.
- Erosion risk.
- Organic-matter contributions.
- Pest-cycle disruption.
- Water use.
- Forage potential.
- Market considerations.

They may show which strategies align with priorities such as conserving water,
generating supplemental income, or improving soil structure.

The brief also suggests brief explanations of how nitrogen-fixing crops, cover
crops, deep-rooting crops, or drought-tolerant crops can contribute to long-term
soil health. The relevance of these benefits still depends on local conditions
and management.

### 5.4 Geospatial mapping and visualization

Teams may use interactive maps to explore conditions and trends over time,
including:

- Long-term soil-moisture patterns.
- Heat waves.
- Water-storage declines.

They may visualize vulnerabilities such as erosion-risk zones, water-stress
hotspots, or frost-prone areas where the available evidence supports the stated
resolution.

Optional additions include timelines, dataset-comparison overlays, and scenario
sliders that adjust rainfall or temperature patterns.

### 5.5 Farmer-centered design

The tool should be understandable to people with limited technical or geospatial
experience.

The brief suggests considering ways for farmers to express priorities or
constraints such as:

- Water availability.
- Equipment limitations.
- Market preferences.

This is not an explicit requirement for a technical questionnaire. The challenge
leaves room for different accessible interaction designs.

Teams should remind users that the tool supports local expertise and identify
where human judgment is especially important.

## 6. Intended outcome and boundaries

The intended outcome is **supportive decision-making**, not an automated
replacement for agricultural judgment.

A useful tool helps people understand:

1. What the observations indicate about growing conditions.
2. Which rotation possibilities are relevant to those conditions.
3. How the options differ.
4. What benefits and risks the evidence suggests.
5. What is unknown or requires local review.

The supplied brief does not require guaranteed yield, profit, or soil-health
outcomes. It repeatedly frames options as possibilities and emphasizes evidence,
uncertainty, and local expertise.

## 7. What the challenge video adds

The opening video emphasizes that farming conditions on Earth are changing:
heat, rainfall, water availability, and soil nutrients all affect what farmers
must do next.

NASA's public Earth observations provide different signals at different scales:
rainfall, soil moisture, heat, vegetation, and water. The mission is to turn those
signals into a tool for exploring agricultural choices.

Its central message is:

> **Compare rotations, reveal trade-offs, understand risk, and make uncertainty
> visible.**

The video invites an SI model, interactive map, visualization, decision-support
tool, or another creative approach. It reinforces flexibility rather than
prescribing a technology stack.

### Challenge team introduced in the supplied transcript

| Person | Role and background described in the video |
|---|---|
| Sadie Burnett Boudro | Challenge author; engineer and developer at NASA Johnson Space Center. Describes work supporting Artemis mission management and integration, Moon base utilization payload integration, low-Earth-orbit research and mission integration, and early development of the Space Reactor Freedom effort. |
| Mani Deep Gogineni | Data solutions architect at NASA Johnson Space Center. Describes data architecture, custom web apps, and tooling supporting Artemis, Moon base payload workflows, and low-Earth-orbit operations. |
| William Stefanov | Senior Earth system scientist at NASA Johnson Space Center and challenge subject-matter expert. Describes work with International Space Station Earth imagery for disaster response and remote-sensing science. |
| Alex Stoken | Data scientist in NASA Johnson Space Center's Earth Science and Remote Sensing Unit. Describes machine-learning work on astronaut photography to extract information for other scientists. |

Names and background descriptions above follow the supplied transcript; they
have not been independently verified against an official staff listing.

These introductions provide context about the challenge team. They do not add
requirements to use astronaut photography, machine learning, or space-mission
software in the solution.

## 8. Resources and possible updates

The brief directs participants to the challenge page's **Resources** tab for data
and supporting materials. It notes that more resources may be added before the
hackathon begins.

The actual Resources-tab contents were not included in the supplied material.
This document therefore does not claim to reproduce that resource collection or
any later updates, evaluation rubric, or submission rules.

## 9. Scope interpretation at a glance

| Central problem to address | Optional approaches or features |
|---|---|
| Connect NASA environmental observations with local agricultural context. | Use every listed satellite or dataset. |
| Help explore crop-rotation strategies and their trade-offs. | Use a particular number of datasets or a particular software stack. |
| Make evidence, uncertainty, and information gaps understandable. | Build machine learning, advanced data fusion, or a live forecast. |
| Support farmer judgment and local expertise. | Collect technical measurements through a questionnaire. |
| Communicate in a farmer-friendly way. | Add maps, sliders, overlays, or other advanced interactions. |

The left column summarizes the challenge's central intent. The right column
lists examples of non-mandatory implementation choices, not features NASA
discourages.

## One-sentence summary

**Use NASA Earth observations and local agricultural knowledge to help farmers
explore crop rotations that could improve soil health and resilience, while
clearly explaining the evidence, trade-offs, risks, and uncertainty.**
