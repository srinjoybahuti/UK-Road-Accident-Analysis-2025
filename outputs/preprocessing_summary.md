# Preprocessing summary

Source file: `data/raw/collisions_2025.csv` (SHA-256 `e699c19bdb82e47e...`, verified unchanged after processing). Processed file: `data/processed/collisions_2025_processed.csv` (61.4 MB).

## Original vs. processed dimensions

|         |   Original |   Processed |
|:--------|-----------:|------------:|
| Rows    |     101525 |      101525 |
| Columns |         44 |          79 |

No rows were removed (0). Columns: -1 dropped (local_authority_district), +36 added (labels, cleaned fields, derived variables and flags).

## Operations and results

1. **Duplicate checks.** Duplicated `collision_index`: 0; duplicated `collision_ref_no`: 0; fully duplicated rows: 0; rows identical in every field except the two IDs: 0; rows where `collision_index` != `collision_year`+`collision_ref_no`: 0. A looser screen (same date, time, easting/northing, vehicles, casualties and force) flags 2 rows (1 pair) with different IDs - listed in `outputs/tables/02_possible_duplicate_pairs.csv`. Different IDs mean they are separately recorded collisions, so they were **kept**. No rows removed.

2. **Date/time conversion.** `date` (DD/MM/YYYY) and `time` (HH:MM) parsed with explicit formats: 0 unparseable dates, 0 unparseable times, 0 dates outside 2025 (range 2025-01-01 to 2025-12-31). The guide's `day_of_week` code (1 = Sunday) agrees with the weekday computed from the date in every row.

3. **Missing-value detection.** True blanks (NaN) exist only in `location_easting_osgr` (2), `location_northing_osgr` (2), `longitude` (2), `latitude` (2) (location fields: 'Null if not known' in the guide); these rows were kept because location is not used in the analysis. All other missingness is encoded with the guide's sentinel `-1` ("Data missing or out of range") - see `outputs/tables/02_missing_value_handling.csv`.

4. **Structural vs. genuine `-1` values.** (a) `local_authority_district` is `-1` in all rows, i.e. carries no information in the 2025 file - the column was dropped (the ONS-code fields `local_authority_ons_district`/`local_authority_highway(_current)` remain). (b) The five legacy-specification fields (`junction_detail_historic`, `pedestrian_crossing_human_control_historic`, `pedestrian_crossing_physical_facilities_historic`, `special_conditions_at_site`, `carriageway_hazards_historic`) are `-1` together in 87,848 rows (86.53%); only 13,677 rows from 17 forces carry legacy values (these are exactly the rows with `collision_injury_based` = 0: verified), and 34 rows are only partly missing. These `-1`s mean 'not collected under this specification', not a data error. The harmonised 2024-specification fields (`junction_detail`, `pedestrian_crossing`, `carriageway_hazards`) are used instead; legacy columns are retained unlabelled. (c) `enhanced_severity_collision` is `-1` exactly when `collision_injury_based` = 0 (verified; 13,677 rows), i.e. the enhanced scale exists only for injury-based reporting. (d) `trunk_road_flag` is `-1` in 7,108 rows, 4,104 of them Police Scotland; `lsoa_of_accident_location` is `-1` in 4,107 rows, 4,104 of them Police Scotland (LSOAs are England/Wales only, as the guide states). (e) `junction_control` never takes the guide's code 0 (0 rows); instead 43,155 of its 44,487 `-1` values occur where `junction_detail` = 0 (not at a junction). These were recoded to 'Not at junction or within 20 metres' (the guide's definition of code 0); the remaining `-1` values were treated as missing.

5. **Invalid values & category consistency (vs. official guide).** Every code in the 23 coded fields exists in the guide (0 unmapped codes; see `outputs/tables/01_code_coverage.csv`). `speed_limit` has 0 values outside the valid set [20, 30, 40, 50, 60, 70]; `number_of_vehicles`/`number_of_casualties` have 0/0 values below 1; coordinates outside a UK bounding box: 0 latitudes, 0 longitudes. `collision_severity` and `enhanced_severity_collision` are mutually consistent in every row (Fatal<->Fatal, Serious<->Very/Moderately/Less serious, Slight<->Slight; where the enhanced value is not `-1`). Road numbers: 0 C/Unclassified roads carry a number and 0 numbered-class roads have number 0. Plausibility flags (flagged, **not removed** - lighting is an officer's judgement): 171 'Daylight' collisions between 00:00 and 03:59 (0.23% of Daylight records; spread across all months, by month: Jan 15, Feb 14, Mar 15, Apr 16, May 17, Jun 20, Jul 17, Aug 10, Sep 12, Oct 9, Nov 10, Dec 16, so not explained by midsummer twilight alone) and 236 'Darkness' collisions between 10:00 and 14:59 (could reflect fog, tunnels or recording error). Flag columns `flag_daylight_small_hours` and `flag_dark_midday` are provided.

6. **Unknown / 'Other' categories.** Codes meaning 'unknown (self reported)' or 'Unknown' (weather 9, road type 9, junction/crossing 99, etc.) and 'Other' (weather 8) are valid guide codes; they were kept as their own labelled categories rather than set to missing, and are shown separately in tables/figures.

7. **Outlier inspection.** Both count variables are right-skewed. The 1.5xIQR rule is degenerate for them (casualties: Q1 = Q3 = 1, so every collision with 2+ casualties, 18,208 = 17.93%, would be flagged; vehicles: 1,939 = 1.91% above the fence), so extremes were inspected through the 99th percentile (vehicles 4, casualties 4) and the maxima (vehicles 17; casualties 142; 29 collisions with >= 10 casualties, 11 with >= 10 vehicles). These are plausible rare multi-vehicle / mass-casualty events that cannot be disproved from the dataset, so **no outliers were removed**; medians and percentiles are reported alongside means. Flag: `flag_multi_casualty_10plus`.

8. **Code-to-label transformation.** 23 coded fields were labelled from the guide's `2024_code_list` sheet (read programmatically, not retyped). Original code columns are retained verbatim; labels are in `severity`, `light`, `weather`, `road_surface`, `area_type`, `police_force_name`, `severity_reporting_basis` and `<field>_label` columns. `-1` becomes a missing label. Guide code 0 for `special_conditions_at_site`/`carriageway_hazards` has a blank label; it is labelled 'None recorded'.

9. **Derived variables.** `datetime`, `month`, `month_name`, `weekday` (from the date), `is_weekend`, `hour`, `time_period` (Night 00-05, Morning 06-09, Midday 10-15, Evening peak 16-19, Late evening 20-23), `is_ksi` (Fatal or Serious), `is_dark` (guide codes 4-7), plus the three plausibility/outlier flag columns.

## Missing-value handling table

| column                                           |   n_nan |   n_minus_one |   pct_missing | interpretation                                                                                     | handling                                                                                |
|:-------------------------------------------------|--------:|--------------:|--------------:|:---------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------|
| local_authority_district                         |       0 |        101525 |        100    | Field empty for the whole 2025 file                                                                | Column dropped                                                                          |
| junction_detail_historic                         |       0 |         87871 |         86.55 | Structural (field not collected under the 2024 specification)                                      | Retained as raw codes; not used in analysis                                             |
| special_conditions_at_site                       |       0 |         87858 |         86.54 | Structural (field not collected under the 2024 specification)                                      | Retained as raw codes; not used in analysis                                             |
| pedestrian_crossing_physical_facilities_historic |       0 |         87851 |         86.53 | Structural (field not collected under the 2024 specification)                                      | Retained as raw codes; not used in analysis                                             |
| pedestrian_crossing_human_control_historic       |       0 |         87852 |         86.53 | Structural (field not collected under the 2024 specification)                                      | Retained as raw codes; not used in analysis                                             |
| carriageway_hazards_historic                     |       0 |         87852 |         86.53 | Structural (field not collected under the 2024 specification)                                      | Retained as raw codes; not used in analysis                                             |
| junction_control                                 |       0 |         44487 |         43.82 | Mostly structural (not at a junction, coded -1 instead of 0)                                       | Recoded to 'Not at junction...' where junction_detail = 0; otherwise NaN                |
| second_road_number                               |       0 |         25105 |         24.73 | Mostly structural (-1 whenever second_road_class is 0 = no second road, or itself missing/unknown) | Set to NaN                                                                              |
| enhanced_severity_collision                      |       0 |         13677 |         13.47 | Structural (only for injury-based reporting)                                                       | Label = NaN; cleaned copy `enhanced_severity_collision_clean`                           |
| trunk_road_flag                                  |       0 |          7108 |          7    | Mostly structural (Police Scotland)                                                                | Label = NaN                                                                             |
| junction_detail                                  |       0 |          6701 |          6.6  | Genuine missing/out of range                                                                       | Label = NaN                                                                             |
| pedestrian_crossing                              |       0 |          6527 |          6.43 | Genuine missing/out of range                                                                       | Label = NaN                                                                             |
| carriageway_hazards                              |       0 |          5346 |          5.27 | Genuine missing/out of range                                                                       | Label = NaN                                                                             |
| lsoa_of_accident_location                        |       0 |          4107 |          4.05 | Structural (England/Wales only)                                                                    | Set to NaN                                                                              |
| road_surface_conditions                          |       0 |           634 |          0.62 | Genuine missing/out of range                                                                       | Label = NaN; rows kept; excluded from surface-specific summaries                        |
| second_road_class                                |       0 |           171 |          0.17 | Genuine missing/out of range                                                                       | Label = NaN                                                                             |
| light_conditions                                 |       0 |            16 |          0.02 | Genuine missing/out of range                                                                       | Label = NaN; rows kept; excluded only from the lighting x severity test (complete-case) |
| first_road_class                                 |       0 |             6 |          0.01 | Genuine missing/out of range                                                                       | Label = NaN; road number set to NaN                                                     |
| first_road_number                                |       0 |             6 |          0.01 | Genuine missing/out of range                                                                       | Set to NaN                                                                              |
| local_authority_highway_current                  |       0 |             2 |          0    | Genuine missing/out of range                                                                       | Set to NaN                                                                              |
| location_easting_osgr                            |       2 |             0 |          0    | Genuine (guide: 'Null if not known')                                                               | Left as NaN; rows kept (location not used)                                              |
| location_northing_osgr                           |       2 |             0 |          0    | Genuine (guide: 'Null if not known')                                                               | Left as NaN; rows kept (location not used)                                              |
| longitude                                        |       2 |             0 |          0    | Genuine (guide: 'Null if not known')                                                               | Left as NaN; rows kept (location not used)                                              |
| latitude                                         |       2 |             0 |          0    | Genuine (guide: 'Null if not known')                                                               | Left as NaN; rows kept (location not used)                                              |

## Outlier inspection

| variable             |   q1 |   q3 |   upper_fence_1.5IQR |   n_above_fence |   pct_above_fence |   max |   n_ge_10 |   p99 |
|:---------------------|-----:|-----:|---------------------:|----------------:|------------------:|------:|----------:|------:|
| number_of_vehicles   |    1 |    2 |                  3.5 |            1939 |              1.91 |    17 |        11 |     4 |
| number_of_casualties |    1 |    1 |                  1   |           18208 |             17.93 |   142 |        29 |     4 |

## Data types in the processed file

|                |   n_columns |
|:---------------|------------:|
| str            |          31 |
| int64          |          27 |
| float64        |           9 |
| bool           |           5 |
| category       |           3 |
| int32          |           2 |
| datetime64[us] |           1 |
| boolean        |           1 |
