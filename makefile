# Process queried TSV.
.PHONY : process
process :
	python3 scripts/normalize.py age_queried.tsv outputs/age_normalized.tsv
	python3 scripts/age_process.py outputs/age_normalized.tsv age_unit_synonyms.tsv outputs/age_output.tsv outputs/age_sorted.tsv outputs/age_unsorted.tsv

# Updates the curated reference TSV based on the manually-curated TSV.
.PHONY : update-curated
update-curated :
	python3 scripts/initialize_curated_tsv.py curation/manual.tsv curation/curated.tsv

# Merges manually curated rows from curated.tsv to a sorted TSV and removes them from an unsorted TSV.
.PHONY : merge
merge :
	python3 scripts/curate.py curation/curated.tsv outputs/age_sorted.tsv outputs/age_unsorted.tsv outputs/merged.tsv outputs/unsortable.tsv

# Makes human-readable versions of the sorted data from merge.tsv.
.PHONY : readable
readable :
	python3 scripts/interpret.py outputs/merged.tsv outputs/typed.tsv

# Removes output TSVs.
.PHONY : clean
clean :
	rm -f outputs/*
