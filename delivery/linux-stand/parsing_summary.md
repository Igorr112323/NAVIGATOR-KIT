# Parsing summary / scope

12 prepared ASCII DXF samples: independent group-code reader (stdlib only)
compared against expected attributes, entity counts, layers and frame bounds.
Results: parsed_stamps.json and parser_diff.log (no differences on last batch run).
12 corresponding PNG are actual saved-DXF renders, not nanoCAD screenshots.
All four fields: DESIGNATION / SHEET / TITLE / FORMAT; no separate mark field.
No general DWG support, nested blocks, INSERT transforms, or GOST geometry certification.
Stdlib-only replay: `python -S tools/check_test_runner_data.py`.
