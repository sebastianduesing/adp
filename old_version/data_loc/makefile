# Process queried TSV.
.PHONY: normalize
normalize :
	python3 scripts/normalize.py data_location.tsv data_normalized.tsv data_loc_word_replacements.tsv data_loc_word_curation.tsv location data_loc

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
	python3 scripts/normalize.py data_location.tsv data_normlaized.tsv data_loc_word_replacements.tsv data_loc_word_curation.tsv location data_loc
# python3 scripts/sort_age.py age_normalized.tsv age_sorted.tsv phrase_normalized_h_age
# python3 scripts/make_curation_tsv.py age_sorted.tsv manual_curation.tsv age_data_type
# python3 scripts/apply_curation.py manual_curation.tsv age_sorted.tsv age_merged.tsv
# python3 scripts/final_processing.py age_merged.tsv age_final.tsv