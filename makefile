# Process queried TSV.
.PHONY: normalize_age
normalize :
	python3 scripts/normalize.py input_files/age_queried.tsv output_files/age_normalized.tsv output_files/age_char_norm_data.tsv word_replacements.tsv output_files/word_curation.tsv h_age age

# Sorts normalized data and creates or updates manual curation TSV.
.PHONY : sort
sort :
	python3 scripts/sort_age.py age_normalized.tsv age_sorted.tsv phrase_normalized_h_age
	python3 scripts/make_curation_tsv.py age_sorted.tsv manual_curation.tsv age_data_type

# Merges manually curated data and autosorted data together.
.PHONY : merge
merge :
	python3 scripts/apply_curation.py manual_curation.tsv age_sorted.tsv age_merged.tsv

# Creates a finalized human-readable age column and calculates confidence in sorting.
.PHONY : final
final :
	python3 scripts/final_processing.py age_merged.tsv age_final.tsv

# Does all of the above.
.PHONY : full
full :
	python3 scripts/normalize.py age_queried.tsv age_normalized.tsv word_replacements.tsv word_curation.tsv h_age age
	python3 scripts/sort_age.py age_normalized.tsv age_sorted.tsv phrase_normalized_h_age
	python3 scripts/make_curation_tsv.py age_sorted.tsv manual_curation.tsv age_data_type
	python3 scripts/apply_curation.py manual_curation.tsv age_sorted.tsv age_merged.tsv
	python3 scripts/final_processing.py age_merged.tsv age_final.tsv
