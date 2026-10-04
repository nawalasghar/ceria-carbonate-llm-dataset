# Extraction prompt

You are extracting experimental data on ceria-based composite electrolytes for
low-temperature SOFCs from a research paper.

Read the paper text in `data/papers/{paper_id}.txt` and write ONE JSON file to
`data/extracted/{paper_id}.json` that follows `schema/extraction_schema.json`
exactly.

Rules:
1. One entry in `materials` per distinct composition the paper reports data for.
2. Use `null` for anything the paper does not state. NEVER guess or infer a value
   that is not written in the paper. Missing metadata is itself a result we want
   to measure.
3. Report conductivity in S/cm (convert mS/cm -> S/cm and note the conversion in
   `notes`). Report power density in mW/cm2.
4. If the paper reports conductivity at several temperatures, use the value
   closest to 600 C and record the actual temperature in `conductivity_temp_C`.
5. `conductivity_type` must be `unspecified` if the paper does not say whether
   the value is total, grain, grain-boundary or ionic.
6. `measurement_method` and `atmosphere` must be `null` if not stated.
7. Set `extraction_confidence` to `low` if the text is an abstract only, or if
   values had to be read from a figure description.
8. Do not write anything except the JSON file.
