# Process queried TSV.
.PHONY: normalize
normalize :
	python3 scripts/normalize.py age_queried.tsv age_normalized.tsv text_swaps.tsv h_age age

# Sorts normalized data and creates or updates manual curation TSV.
.PHONY : sort
sort :
	python3 scripts/sort_age.py age_normalized.tsv age_sorted.tsv normalized_h_age_style=age
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
	python3 scripts/normalize.py age_queried.tsv age_normalized.tsv text_swaps.tsv h_age age
	python3 scripts/sort_age.py age_normalized.tsv age_sorted.tsv normalized_h_age_style=age
	python3 scripts/make_curation_tsv.py age_sorted.tsv manual_curation.tsv age_data_type
	python3 scripts/apply_curation.py manual_curation.tsv age_sorted.tsv age_merged.tsv
	python3 scripts/final_processing.py age_merged.tsv age_final.tsv
