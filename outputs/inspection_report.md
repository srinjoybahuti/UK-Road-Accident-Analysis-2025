# Step 1 - Raw data and data-guide inspection

- **Collision file:** `data/raw/collisions_2025.csv` (19.3 MB), UTF-8 (no BOM), comma-separated, header row present.
- **Guide file:** `data/reference/data_guide_2025.xlsx` - sheets: `2024_code_list` (1825 rows x 5 cols), `2011_to_2024_conversion` (102 rows x 7 cols).
- **Dimensions:** 101,525 rows x 44 columns; dtypes: {'int64': 30, 'str': 8, 'float64': 6}.
- `collision_year` takes only the value(s) [2025].
- Columns whose names differ between CSV and guide: {'enhanced_severity_collision': 'enhanced_collision_severity', 'collision_adjusted_severity_serious': 'collision_adjusted_serious', 'collision_adjusted_severity_slight': 'collision_adjusted_slight'}.
- CSV columns with no entry in the guide's collision table: none.
- Columns containing NaN (true blanks): `location_easting_osgr` (2), `location_northing_osgr` (2), `longitude` (2), `latitude` (2).
- Coded fields with codes absent from the guide: none.

## Column profile

| column                                           | dtype   |   n_missing_nan |   n_minus_one |   n_unique | in_guide   | guide_name                  |
|:-------------------------------------------------|:--------|----------------:|--------------:|-----------:|:-----------|:----------------------------|
| collision_index                                  | str     |               0 |             0 |     101525 | True       |                             |
| collision_year                                   | int64   |               0 |             0 |          1 | True       |                             |
| collision_ref_no                                 | str     |               0 |             0 |     101525 | True       |                             |
| location_easting_osgr                            | float64 |               2 |             0 |      83236 | True       |                             |
| location_northing_osgr                           | float64 |               2 |             0 |      83768 | True       |                             |
| longitude                                        | float64 |               2 |             0 |      88044 | True       |                             |
| latitude                                         | float64 |               2 |             0 |      82164 | True       |                             |
| police_force                                     | int64   |               0 |             0 |         44 | True       |                             |
| collision_severity                               | int64   |               0 |             0 |          3 | True       |                             |
| number_of_vehicles                               | int64   |               0 |             0 |         13 | True       |                             |
| number_of_casualties                             | int64   |               0 |             0 |         21 | True       |                             |
| date                                             | str     |               0 |             0 |        365 | True       |                             |
| day_of_week                                      | int64   |               0 |             0 |          7 | True       |                             |
| time                                             | str     |               0 |             0 |       1440 | True       |                             |
| local_authority_district                         | int64   |               0 |        101525 |          1 | True       |                             |
| local_authority_ons_district                     | str     |               0 |             0 |        351 | True       |                             |
| local_authority_highway                          | str     |               0 |             0 |        208 | True       |                             |
| local_authority_highway_current                  | str     |               0 |             2 |        208 | True       |                             |
| first_road_class                                 | int64   |               0 |             6 |          7 | True       |                             |
| first_road_number                                | int64   |               0 |             6 |       3110 | True       |                             |
| road_type                                        | int64   |               0 |             0 |          6 | True       |                             |
| speed_limit                                      | int64   |               0 |             0 |          6 | True       |                             |
| junction_detail_historic                         | int64   |               0 |         87871 |         11 | True       |                             |
| junction_detail                                  | int64   |               0 |          6701 |          8 | True       |                             |
| junction_control                                 | int64   |               0 |         44487 |          6 | True       |                             |
| second_road_class                                | int64   |               0 |           171 |          9 | True       |                             |
| second_road_number                               | int64   |               0 |         25105 |       2487 | True       |                             |
| pedestrian_crossing_human_control_historic       | int64   |               0 |         87852 |          5 | True       |                             |
| pedestrian_crossing_physical_facilities_historic | int64   |               0 |         87851 |          8 | True       |                             |
| pedestrian_crossing                              | int64   |               0 |          6527 |         10 | True       |                             |
| light_conditions                                 | int64   |               0 |            16 |          6 | True       |                             |
| weather_conditions                               | int64   |               0 |             0 |          9 | True       |                             |
| road_surface_conditions                          | int64   |               0 |           634 |          7 | True       |                             |
| special_conditions_at_site                       | int64   |               0 |         87858 |         10 | True       |                             |
| carriageway_hazards_historic                     | int64   |               0 |         87852 |          8 | True       |                             |
| carriageway_hazards                              | int64   |               0 |          5346 |         14 | True       |                             |
| urban_or_rural_area                              | int64   |               0 |             0 |          3 | True       |                             |
| did_police_officer_attend_scene_of_accident      | int64   |               0 |             0 |          3 | True       |                             |
| trunk_road_flag                                  | int64   |               0 |          7108 |          3 | True       |                             |
| lsoa_of_accident_location                        | str     |               0 |          4107 |      27179 | True       |                             |
| enhanced_severity_collision                      | int64   |               0 |         13677 |          6 | True       | enhanced_collision_severity |
| collision_injury_based                           | int64   |               0 |             0 |          2 | True       |                             |
| collision_adjusted_severity_serious              | float64 |               0 |             0 |       6557 | True       | collision_adjusted_serious  |
| collision_adjusted_severity_slight               | float64 |               0 |             0 |       6557 | True       | collision_adjusted_slight   |

## Code coverage against the official guide

| column                                           |   n_codes_in_guide |   n_distinct_in_data | codes_not_in_guide   |   rows_not_in_guide |   n_minus_one |   pct_minus_one |
|:-------------------------------------------------|-------------------:|---------------------:|:---------------------|--------------------:|--------------:|----------------:|
| police_force                                     |                 52 |                   44 | []                   |                   0 |             0 |            0    |
| collision_severity                               |                  3 |                    3 | []                   |                   0 |             0 |            0    |
| enhanced_severity_collision                      |                  6 |                    6 | []                   |                   0 |         13677 |           13.47 |
| day_of_week                                      |                  7 |                    7 | []                   |                   0 |             0 |            0    |
| first_road_class                                 |                  7 |                    7 | []                   |                   0 |             6 |            0.01 |
| road_type                                        |                  8 |                    6 | []                   |                   0 |             0 |            0    |
| junction_detail_historic                         |                 11 |                   11 | []                   |                   0 |         87871 |           86.55 |
| junction_detail                                  |                  8 |                    8 | []                   |                   0 |          6701 |            6.6  |
| junction_control                                 |                  7 |                    6 | []                   |                   0 |         44487 |           43.82 |
| second_road_class                                |                  9 |                    9 | []                   |                   0 |           171 |            0.17 |
| pedestrian_crossing_human_control_historic       |                  5 |                    5 | []                   |                   0 |         87852 |           86.53 |
| pedestrian_crossing_physical_facilities_historic |                  8 |                    8 | []                   |                   0 |         87851 |           86.53 |
| pedestrian_crossing                              |                 10 |                   10 | []                   |                   0 |          6527 |            6.43 |
| light_conditions                                 |                  6 |                    6 | []                   |                   0 |            16 |            0.02 |
| weather_conditions                               |                 10 |                    9 | []                   |                   0 |             0 |            0    |
| road_surface_conditions                          |                  9 |                    7 | []                   |                   0 |           634 |            0.62 |
| special_conditions_at_site                       |                 10 |                   10 | []                   |                   0 |         87858 |           86.54 |
| carriageway_hazards_historic                     |                 10 |                    8 | []                   |                   0 |         87852 |           86.53 |
| carriageway_hazards                              |                 14 |                   14 | []                   |                   0 |          5346 |            5.27 |
| urban_or_rural_area                              |                  4 |                    3 | []                   |                   0 |             0 |            0    |
| did_police_officer_attend_scene_of_accident      |                  4 |                    3 | []                   |                   0 |             0 |            0    |
| trunk_road_flag                                  |                  3 |                    3 | []                   |                   0 |          7108 |            7    |
| collision_injury_based                           |                  2 |                    2 | []                   |                   0 |             0 |            0    |

## Local-authority code coverage

| column                          |   n_distinct |   rows_with_code_not_in_guide_list | codes_not_in_guide_list                                                        |
|:--------------------------------|-------------:|-----------------------------------:|:-------------------------------------------------------------------------------|
| local_authority_ons_district    |          351 |                               1202 | ['E08000038', 'E08000039']                                                     |
| local_authority_highway         |          208 |                               3998 | ['E06000063', 'E06000064', 'E06000065', 'E06000066', 'E08000038', 'E08000039'] |
| local_authority_highway_current |          208 |                                  0 | ["guide provides no code list ('See latest ONS code list')"]                   |
| local_authority_district        |            1 |                                  0 | ['all 101525 rows are -1']                                                     |

Note: the guide's sheet is titled `2024_code_list`; it is the only code list supplied and is used for the 2025 file. The sheet `2011_to_2024_conversion` documents how legacy (2011-specification) fields map to the 2024 specification.