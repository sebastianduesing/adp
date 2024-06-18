# Normalize data in TSV.
.PHONY: normalize_age
normalize_age :
	python3 scripts/normalize.py input_files/age_queried.tsv output_files/age_normalized.tsv output_files/age_char_norm_data.tsv word_replacements.tsv output_files/word_curation.tsv h_age age

.PHONY: normalize_data_loc
normalize_data_loc :
	python3 scripts/normalize.py input_files/data_location_tab_removed.tsv output_files/data_normalized.tsv output_files/data_loc_char_norm_data.tsv data_loc_word_replacements.tsv output_files/data_loc_word_curation.tsv location data_loc

# Generate manual-review files with phony lines.
.PHONY: create_review_files
create_review_files:
	python3 scripts/pull_random_lines.py age output_files/age_normalized.tsv 100 analysis/phony_lines_age.tsv analysis/review_sample_age.tsv analysis/phony_tracker_age.txt
	python3 scripts/pull_random_lines.py data_loc output_files/data_normalized.tsv 100 analysis/phony_lines_data_loc.tsv analysis/review_sample_data_loc.tsv analysis/phony_tracker_data_loc.txt

# Calculate normalization metrics.
.PHONY: calculate_metrics
calculate_metrics:
	python3 scripts/collect_normalization_data.py age output_files/age_char_norm_data.tsv
	python3 scripts/collect_normalization_data.py data_loc output_files/data_loc_char_norm_data.tsv
	python3 scripts/calculate_metrics.py output_files/age_normalized.tsv h_age analysis age
	python3 scripts/calculate_metrics.py output_files/data_normalized.tsv location analysis data_loc
	python3 scripts/score_evaluator.py age output_files/age_normalized.tsv h_age output_files/score_data.tsv
	python3 scripts/score_evaluator.py data_loc output_files/data_normalized.tsv location output_files/score_data.tsv
	
# Sorts normalized data and creates or updates manual curation TSV.
.PHONY : sort
sort :
	python3 scripts/age_sort.py age/output_files/age_normalized.tsv age/processing/age_sorted.tsv phrase_normalized_h_age
	python3 scripts/age_make_curation_tsv.py age/processing/age_sorted.tsv age/processing/manual_curation.tsv age_data_type

# Merges manually curated data and autosorted data together.
.PHONY : merge
merge :
	python3 scripts/age_apply_curation.py age/processing/manual_curation.tsv age/processing/age_sorted.tsv age/processing/age_merged.tsv

# Creates a finalized human-readable age column and calculates confidence in sorting.
.PHONY : final
final :
	python3 scripts/age_process_final.py age/processing/age_merged.tsv age/processing/age_final.tsv
