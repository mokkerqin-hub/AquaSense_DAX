# AquaSense

**Ranking which water treatment plants to repair first, by the water they could actually recover.**

Data–AI–Experience (DAX) Challenge · Team 5G Data · Universiti Malaysia Pahang Al-Sultan Abdullah

---

## Why

Pahang loses about a third of the water it treats. PAIP ranks its 74 plants by **loss percentage**, but percentage divides out plant size and repair crews recover **cubic metres**.

The two rankings share **no plants** in their top ten:

| Plant | Loss rate | Water lost |
|---|---|---|
| Semambu | 27.2% — lowest of all 74 | 12.7 Mm³/yr |
| Bera Kompleks | 59.3% | 0.9 Mm³/yr |

The most efficient plant in Pahang leaks fourteen times more water than one of the worst.

## What it does

Ranks all 74 plants by a **Leakage Intervention Priority Score** — recoverable water adjusted for repair difficulty — then shows what a chosen repair programme does to the 2030 target.

| Control | Question | Default |
|---|---|---|
| Water or speed | Most water, or quickest fix? | 0.70 |
| Community need | Should districts that struggle the most with water cut go first? | 0.00 |
| Crew capacity | How many plants can you repair? | 10 |
| Repair effectiveness | How much leakage does a repair stop? | 0.40 |

## The score

```
Vᵢ    = annual physical loss                          (leakage only — meter error needs a different fix)
Dᵢ    = ⅓[ ln(Lᵢ)~ + Aᵢ~ + (1 − Bᵢ~) ]                (pipe length, plant age, inverted burst rate)
LIPSᵢ = 100 × [ w·rankpt(Vᵢ) + (1−w)·rankpt(1−Dᵢ) ]   (percentile ranks — see note)
PRIᵢ  = LIPSᵢ × ( 1 + α·DVI_d(i) )                    (DVI from DOSM 2024 poverty and income)
```

Volume varies ~163× across plants, difficulty only ~4.8×. Combining raw values lets volume swamp difficulty entirely, so both are converted to percentile ranks first.

## Results

**Ten plants hold 47% of Pahang's recoverable water** — repairing them cuts projected 2030 NRW from 31.7% to 27.5%. Reaching the 25% target needs ~25 plants.

Raising community need to α = 0.3 shifts repairs toward Bera and Jerantut and recovers **41.5% less water**. That trade-off is the point — the tool quantifies it rather than hiding it.

District poverty does **not** predict water loss (*r* = 0.07); loss tracks network geography, with rural plants averaging 47% against 31% urban. Community need is a normative weighting, not a technical correction.

## Run it

**[Try it live →](https://aquasensedax-f6lm7gfvipv5k9sakjcwkf.streamlit.app/)**

Or run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

`lips_queue.csv` and `nrw_forecast.csv` are pre-computed — the app does only arithmetic at runtime, so the sliders stay instant.

## Limitations

Difficulty is a structural proxy, not repair cost. DVI is district-level so all plants in a district share one weighting. The forecast is 36 months extrapolated 60 — read 2030 values as trajectory, not point estimates.

## Data

2,664 plant-month records (PAIP: prasiswazah.csv) and district statistics (DOSM: pahang_district_master.csv). Forecast is a damped Holt model, selected from four models on held-out validation.

---
