# E7 mustard audit — 2026-11-06

## Verdict

- W1 mapping is correct. The 29/35 was **not** a W1 bug and **not** a real 50 mm/day frequency.
- `Data/POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv` (`A`) has
  `PRECTOTCORR` exactly **24×** the live POWER API and the 2000 CSV (`B`).
  `T2M`, `T2M_MAX`, `T2M_MIN`, `QV2M`, and `GWETTOP` match.
- Corrected mustard heavy-rain result is **1/35** (season 2023, 2024-01-21, 70.23 mm/day).
  `B` only (2000–2025): **1/26**. This is weakly informative (near 0).
- Mustard warning stays **disabled** by config. Statistics only; wheat warnings likewise off.

## CSV audit

| Check | Result |
|---|---|
| A rows / range | 13,445; 1990-01-01 → 2026-10-23 |
| B rows / range | 9,790; 2000-01-01 → 2026-10-20 |
| Overlap / A-only | 9,790 / 3,655; B-only 0 |
| Duplicate dates | 0 in each file |
| Bad row lengths | 0 in each file |
| T2M/QV2M/GWETTOP overlap | match (median ratio 1.0) |
| PRECTOTCORR overlap | A = 24× B on 6,175 nonzero days (median ratio 24.0) |
| 1991–1999 | only in A; live API samples confirm the same 24× factor |
| Events outside Nov 6–Feb 7 span | 0 |

Live API samples: 2000-01-15 A 0.72 vs API 0.03; 2000-01-16 A 36.72 vs API 1.53;
1991-01-02 A 1.68 vs API 0.07; 1991-01-03 A 28.32 vs API 1.18.

## W1 mapping check

| Season start | Mapped period | Days | Valid |
|---|---|---|---|
| 1991 | 1991-11-06 → 1992-02-07 | 94 | 94 |
| 2000 | 2000-11-06 → 2001-02-07 | 94 | 94 |
| 2024 (leap) | 2024-11-06 → 2025-02-07 | 94 | 94 |

35 seasons evaluated (1991–2025), 0 excluded; all mapped dates match the month/day span.

## Raw A seasons with any day >50 mm/day (29 seasons, 91 events)

```text
1991: 1991-12-25=157.44; 1991-12-26=295.2
1992: 1993-01-08=135.12; 1993-01-09=84.72; 1993-02-01=129.84
1993: 1994-01-16=149.52; 1994-01-31=54.72
1994: 1995-01-10=57.36
1995: 1995-11-09=57.12; 1995-11-10=438.0; 1995-11-11=228.24; 1996-01-17=79.92
1996: 1997-01-21=71.28; 1997-02-02=83.28
1997: 1997-11-13=101.04; 1997-12-10=248.16; 1998-01-21=252.96; 1998-01-28=60.48
1998: 1998-11-10=103.68; 1998-11-11=80.16; 1998-11-22=234.0; 1998-11-23=142.8
1999: 2000-01-24=61.44; 2000-02-02=87.84; 2000-02-05=339.6; 2000-02-06=224.88
2001: 2002-01-28=149.52
2002: 2002-11-12=630.24; 2002-11-13=69.12; 2003-02-01=51.36; 2003-02-02=55.44
2003: 2003-12-28=153.6; 2004-01-24=142.08
2004: 2005-01-11=50.16; 2005-01-18=119.76
2006: 2007-02-07=117.84
2007: 2007-11-15=152.4; 2007-11-16=202.56; 2008-01-23=173.52; 2008-01-24=98.88; 2008-01-25=91.2; 2008-01-26=125.76; 2008-01-30=302.4
2008: 2008-11-25=76.08; 2008-11-26=119.28; 2009-02-07=363.36
2010: 2010-12-08=189.12; 2010-12-09=586.8; 2010-12-10=111.36
2011: 2012-01-02=67.44; 2012-01-09=68.4
2012: 2012-11-06=178.32; 2012-12-12=81.12
2014: 2015-01-03=57.36; 2015-01-04=144.72
2015: 2016-01-20=575.76
2017: 2017-11-15=82.08; 2017-11-16=82.32; 2017-12-09=191.04; 2017-12-10=637.92; 2017-12-11=91.2
2018: 2018-12-17=102.96; 2018-12-18=334.32
2019: 2019-11-09=249.12; 2019-11-10=168.0; 2019-12-27=113.76; 2020-01-03=326.88; 2020-01-04=185.52; 2020-01-09=78.24; 2020-01-29=75.6; 2020-01-30=70.56
2021: 2021-11-14=181.44; 2021-11-15=68.4; 2021-12-06=353.28; 2022-01-11=55.44; 2022-01-12=139.68; 2022-01-13=104.4; 2022-01-14=105.84; 2022-02-04=798.72; 2022-02-06=82.08
2022: 2022-12-27=51.6
2023: 2023-12-07=664.8; 2023-12-08=360.0; 2023-12-09=121.44; 2023-12-29=90.0; 2024-01-18=65.04; 2024-01-19=90.96; 2024-01-20=189.36; 2024-01-21=1685.52
2024: 2024-11-07=57.84
2025: 2026-01-14=74.4
```

Raw A/24 leaves only `2024-01-21 = 70.23 mm/day` above 50. All raw event dates are
inside the Nov 6 → Feb 7 month/day span.

## Corrected X of Y

| Data | Seasons | X (≥1 day >50) | Y | X/Y |
|---|---:|---:|---:|---:|
| A raw (buggy 24×) | 1991–2025 | 29 | 35 | 82.9% |
| A ÷ 24 | 1991–2025 | 1 | 35 | 2.9% |
| B only | 2000–2025 | 1 | 26 | 3.8% |
| A÷24 (1991–99) + B (2000–25) | 1991–2025 | 1 | 35 | 2.9% |

**Decision:** keep mustard `disabled` by config (option D, statistics only). The warning
code/tests stay available for a future stage-specific window. Production E7 uses the
POWER API, which matches B; the local A `PRECTOTCORR` column must not be used raw.
