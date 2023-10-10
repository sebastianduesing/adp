# Process queried TSV.
.PHONY : process
process :
	python3 scripts/normalize.py age_queried.tsv outputs/age_normalized.tsv
	python3 scripts/age_process.py outputs/age_normalized.tsv age_unit_synonyms.tsv outputs/age_output.tsv outputs/age_sorted.tsv outputs/age_unsorted.tsv


# Removes output TSVs.
.PHONY : clean
clean :
	rm -f outputs/*
