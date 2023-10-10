# Process queried TSV.
.PHONY : process
process :
	python3 normalize.py age_queried.tsv age_normalized.tsv
	python3 age_process.py age_normalized.tsv age_unit_synonyms.tsv


# Removes output TSVs.
.PHONY : clean
clean :
	rm -f age_normalized.tsv age_output.tsv age_sorted.tsv age_unsorted.tsv age_manual.tsv


# Duplicates age_unsorted.tsv for manual sorting.
age_manual.tsv : age_unsorted.tsv
	cp age_unsorted.tsv age_manual.tsv

