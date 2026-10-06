# Nature Bingo

A bingo card of the 16 things most likely to be out near your town this October. Open it, put the phone away, and go find them. Tap a square when you do, or print the card.

**[Open the app](https://naturebingo.vercel.app)** · [DEV post](https://dev.to/jonathansolvesstuff/i-walked-an-open-models-bingo-card-through-a-town-with-almost-no-nature-records-i-found-2-of-16-649) · [Demo video](https://www.youtube.com/watch?v=Xo2zRxRYsWE) · [Short](https://www.youtube.com/shorts/UwPOgILmLak) · [Blog](https://jonathanandrei.com/blog/nature-bingo-printable-card-tabpfn-inaturalist/) · [My walk on iNaturalist](https://www.inaturalist.org/observations/jonathansolvesproblems)

Built for the DEV Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass. [Submission post](https://dev.to/jonathansolvesstuff/i-walked-an-open-models-bingo-card-through-a-town-with-almost-no-nature-records-i-found-2-of-16-649).

## Why small towns

A "what was seen near here last October" list works in a city. It does not work in a small town. Around Hawkesbury, Ontario, iNaturalist has about 3,000 research-grade records in total, and the most-logged species across every October on record has four sightings.

So the card borrows from the neighbours. [TabPFN](https://github.com/PriorLabs/TabPFN), an open-weight tabular model, learns from ten years of Octobers (2016 to 2025) across 48 towns between Ottawa and Montreal. For each candidate species in each town it sees what was logged there before and across the region, and ranks what that town should expect this month. It runs on a laptop GPU: Hawkesbury's card ranks in about 19 seconds, with nothing sent to a model API.

## Graded by what people photographed

The model trained on target years up to 2024. October 2025 was held out, each town's card was made blind, and the score is how many of its 16 squares somebody actually photographed and logged on iNaturalist that month. Same towns, same month, four methods:

| Method | Squares photographed, of 16 (mean over 48 towns) |
|---|---|
| TabPFN | 5.02 |
| The town's own past Octobers | 4.44 |
| Gradient boosting (scikit-learn) | 4.33 |
| Regional most-seen | 3.65 |

Against the town's own past Octobers, TabPFN was better in 23 towns, the same in 14 and worse in 11.

What is not claimed: in the 16 towns with the least October history, gradient boosting found 2.19 squares on average and TabPFN 1.88 (last October's list: 1.19). Hawkesbury is one of the towns where TabPFN lost, 3 against 6. The grader also rewards guessing what people photograph, which tilts towards big, common, daytime things near paths. Full numbers: [results/backtest.json](results/backtest.json), [results/backtest_bands.json](results/backtest_bands.json).

## The walk

On 6 October 2026, from 10:18 to 10:54, I took Hawkesbury's card to Confederation Park on the Ottawa River. In about half an hour I confirmed 2 of the 16 by photo: Canada geese and a mallard drake. Both observations reached Research Grade on iNaturalist, identified independently by another observer. Ring-billed gulls are marked probable, because the ring on the bill is not visible in my photos, and that observation is still waiting for a second opinion. Record: [data/walks.json](data/walks.json).

The photos went to iNaturalist, so next October's card for Hawkesbury will learn from them.

## How it works

```
scripts/towns.py     geocode 48 small towns between Ottawa and Montreal
scripts/pull.py      iNaturalist species counts per town and year (10 km local, 50 km regional, research grade)
scripts/features.py  one row per (town, target year, species), features from earlier years only
scripts/backtest.py  blind test on October 2025, four methods
scripts/sparse.py    results split by how much history each town had
scripts/card.py      this October's cards for every town
scripts/taxa.py      openly licensed photo and credit for each species
site/                the app: static HTML, cards.json, walks.json
```

## Run it

Python 3.12 with [uv](https://docs.astral.sh/uv/) and an NVIDIA GPU. The TabPFN weights are open but gated: accept the license once at [ux.priorlabs.ai](https://ux.priorlabs.ai/account/licenses) and put your token in `TABPFN_TOKEN` (or `~/.cache/tabpfn/auth_token`).

```
uv sync
uv run python scripts/towns.py
uv run python scripts/pull.py        # about 35 minutes, cached and resumable
uv run python scripts/features.py
uv run python scripts/backtest.py    # about 11 minutes on an 8 GB laptop GPU
uv run python scripts/card.py        # all 48 towns, or name some: card.py Hawkesbury
uv run python scripts/taxa.py --refresh-cards
```

Then serve `site/` with any static server (copy `data/cards.json` and `data/walks.json` into it).

## Sources

- About 3,000 research-grade iNaturalist records within 10 km of Hawkesbury (3,125 from the API on 5 Oct 2026, 3,100 on the site on 6 Oct 2026): [iNaturalist observations API](https://api.inaturalist.org/v1/observations?lat=45.6103&lng=-74.6056&radius=10&quality_grade=research&per_page=1)
- The most-logged species near Hawkesbury across every October on record has 4 sightings: [iNaturalist species counts API](https://api.inaturalist.org/v1/observations/species_counts?lat=45.607&lng=-74.605&radius=10&month=10&quality_grade=research)
- Ten years of Octobers (2016 to 2025) across 48 towns: [scripts/pull.py](scripts/pull.py), [data/towns.json](data/towns.json)
- TabPFN's card beat the town's own last-October list in 23 towns, tied in 14 and lost in 11, and photographed 3 of 16 squares for Hawkesbury: [results/backtest.json](results/backtest.json)
- Results by how much October history a town had: [results/backtest_bands.json](results/backtest_bands.json), from [scripts/sparse.py](scripts/sparse.py)
- The walk on 6 Oct 2026, 10:18 to 10:54, Confederation Park: [data/walks.json](data/walks.json)
- My observations: [Canada Goose](https://www.inaturalist.org/observations/406393901), [Mallard](https://www.inaturalist.org/observations/406393902), [Ring-billed Gull](https://www.inaturalist.org/observations/406393900)

Data from iNaturalist. Card photos are iNaturalist photos under their own open licences, credited on each card. Walk photos and drone footage are mine.

## License

MIT, see [LICENSE](LICENSE). TabPFN weights are under Prior Labs' own license.
