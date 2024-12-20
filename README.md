# Adaptable, User-Dependent, and Precise Free-Text Normalization

ADP is a set of scripts for standardizing free-text datasets in TSV form. ADP uses a three-stage approach that applies standardization at the level of characters, words, and phrases.

Included in this repository are two datasets containing age and data-location free-text data from the Immune Epitope Database (IEDB).

The scripts [`char_normalizer.py`](scripts/char_normalizer.py), [`word_normalizer.py`](scripts/word_normalizer.py), and [`phrase_normalizer.py`](scripts/phrase_normalizer.py) perform the core normalization functions in ADP, but the [`scripts/`](scripts/) directory contains several other scripts that provide accessory functions and perform data collection and analysis on the outputs of the normalization process.

## Using ADP

### Setting up for a new dataset

ADP needs a specific folder structure to work on a dataset. To run ADP on a TSV of data, do the following steps. The linked paths point to the corresponding directories and files for the age dataset as examples.

1. Create a main directory for that "style" of data, like the directory [`age/`](age/).
2. Create the following directories in the parent directory: [`input_files/`](age/input_files/), [`output_files`](age/output_files/).
3. Put your TSV file of data in [`<style>/input_files/`](age/input_files/age.tsv)
4. Optional: Also create these directories: [`<style>/analysis/`](age/analysis/) and [`<style>/analysis/figures/`](age/analysis/figures).

### Calling the scripts

The [`character normalization script`](scripts/char_normalizer.py) requires 3 arguments:
1. Style: the name of the parent directory for that dataset, e.g., [`"age"`](age/).
2. File name: the name of the TSV of data to be normalized, not including its path, e.g., [`"age.tsv"`](age/input_files/age.tsv)/
3. Target column: the name of the column of data to normalize, e.g., "h_age".

To call this script on the age dataset, try:
```
python3 scripts/char_normalizer.py age age.tsv h_age
```

The [`word`](scripts/word_normalizer.py) and [`phrase normalization scripts`](scripts/phrase_normalizer.py) only require 2 arguments:
1. Style: the name of the parent directory for that dataset, e.g., [`"age"`](age/)
2. Target column: the name of the column of data to normalize, e.g., "h_age".

To call these scripts on the age dataset, try:
```
python3 scripts/word_normalizer.py age h_age
```
```
python3 scripts/phrase_normalizer.py age h_age
```
Generally, the scripts in this repository attempt to adhere to a convention of requiring arguments in a general-to-specific order, e.g., directory, filename, column.

### Normalizing data

Running the [`character normalization script`](scripts/char_normalizer.py) will create two files: a [`review file`](age/output_files/char_review.tsv) and an [`character normalized output file`](age/output_files/c_norm_age.tsv). By editing the action columns in the review file, you can create rules that direct the behavior of the character normalization script next time you run it on the dataset. The action columns are as follows:

- replace_with: Adding text in this column within a row directs the script to replace the character listed in that row with the text in that column.
- remove: Adding any text in this column within a row directs the script to remove the character listed in that row wherever it occurs in the data.
- invalidate: Adding any text in this column within a row directs the script to fail validation on data items that contain the character listed in that row.
- allow: Adding any text in this column within a row directs the script to accept that character as a known & permitted character that will not trigger data items to fail validation.

Numbers and lowercase letters are automatically treated as allowed characters and do not appear in the review file.

Once you make an action decision (by adding text to an action column) on at least one row in the review file, when you re-run the character normalizer script, the script will transfer the line(s) with action decisions to a [`reference file`](age/output_files/char_reference.tsv), and the actions you specified will be applied to the output file. You can also edit the reference file to change the behavior of the script in future runs.

The [`word normalization script`](scripts/word_normalizer.py) functions the same way, with words instead of characters.

More coming soon on the phrase normalization script.


