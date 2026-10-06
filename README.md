# Nature Bingo

A printable bingo card of what is most likely to be out this week within a walk of your door. Print it, leave the phone at home, and go find it.

The card is built from public iNaturalist observations and a tabular model (TabPFN, open weights) that runs locally. It is meant for small towns, where too few people log sightings for a simple "most seen last October" list to work.

Entry for the DEV Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass. Work in progress.

## Sources

- About 3,000 research-grade iNaturalist records within 10 km of Hawkesbury (3,125 from the API on 5 Oct 2026, 3,100 on the site on 6 Oct 2026): [iNaturalist observations API](https://api.inaturalist.org/v1/observations?lat=45.6103&lng=-74.6056&radius=10&quality_grade=research&per_page=1)
- The most-logged species near Hawkesbury across every October on record has 4 sightings: [iNaturalist species counts API](https://api.inaturalist.org/v1/observations/species_counts?lat=45.607&lng=-74.605&radius=10&month=10&quality_grade=research)
- Ten years of Octobers (2016 to 2025) across 48 towns: [scripts/pull.py](scripts/pull.py), [data/towns.json](data/towns.json)
- TabPFN's card beat the town's own last-October list in 23 towns, tied in 14 and lost in 11, and photographed 3 of 16 squares for Hawkesbury: [results/backtest.json](results/backtest.json)
- Results by how much October history a town had: [results/backtest_bands.json](results/backtest_bands.json), from [scripts/sparse.py](scripts/sparse.py)
- The walk on 6 Oct 2026, 10:18 to 10:54, Confederation Park: [data/walks.json](data/walks.json)

## License

MIT
