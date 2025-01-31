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

Running the [`character normalization script`](scripts/char_normalizer.py) will create two files: a [`review file`](age/output_files/char_review.tsv) and an [`character normalized output file`](age/output_files/c_norm_age.tsv). The first time you run the character normalization script, it will apply no changes. By editing the action columns in the review file, you can create rules that direct the behavior of the character normalization script next time you run it on the dataset. The action columns are as follows:

- replace_with: Adding text in this column within a row directs the script to replace the character listed in that row with the text in that column.
- remove: Adding any text in this column within a row directs the script to remove the character listed in that row wherever it occurs in the data.
- invalidate: Adding any text in this column within a row directs the script to fail validation on data items that contain the character listed in that row.
- allow: Adding any text in this column within a row directs the script to accept that character as a known & permitted character that will not trigger data items to fail validation.

Numbers and lowercase letters are automatically treated as allowed characters and do not appear in the review file.

Once you make an action decision (by adding text to an action column) on at least one row in the review file, when you re-run the character normalizer script, the script will transfer the line(s) with action decisions to a [`reference file`](age/output_files/char_reference.tsv), and the actions you specified will be applied to the output file. You can also edit the reference file to change the behavior of the script in future runs.

The [`word normalization script`](scripts/word_normalizer.py) functions the same way, with words instead of characters.

The [`word review file`](age/output_files/word_review.tsv) and [`word reference file`](age/output_files/word_reference.tsv) also contain a `category` column that will be used in the phrase normalization stage to identify phrase structures based on word categories, e.g., in the age dataset, "year" and "month" are categorized as "unit", and "mean" and "median" are categorized as "statistical". Entering any text in this column will make the phrase normalization script interpret occurrences of that word as an instance of that category, e.g., identifying "1 year" as an instance of the `[number][unit]` phrase structure.

Running the [`phrase normalization script`](scripts/char_normalizer.py) will create a [`phrase type sheet`](age/output_files/age_phrase_types.tsv) and a [`phrase normalized output file`](age/output_files/p_norm_age.tsv). The first time you run the phrase normalization script, it will apply no changes.  By adding rows to the phrase type sheet, you can direct how the phrase normalization script standardizes phrases in future runs of the script. The columns are as follows:

- `name`: A label for the phrase structure. This does not need to be distinct; in fact, it may be useful to identify several different patterns as types of ranges, for instance.
- `pattern`: A string taken from the `phrase_type_string` column of the [`phrase-normalized output file`](age/output_files/p_norm_age.tsv). This is the basic format of of a set of data items, and it takes the form of a list of categories with an index in parenthesis reflecting the order in which they occur in the string, e.g., "1 year" and "6 months" both have the phrase type string `[number(0)][unit(1)]`.
- `valid?`: An indicator of whether or not the pattern should be invalidated. If "Y" is in this column, the dataset will be standardized according to the standard form in the next column. If "N" is in this column, the string will fail phrase-stage validation and will not be standardized. This can be used to eliminate un-useful data items, like numbers without units in the age dataset.
- `standard_form`: A pattern to which the string will be reformatted. Standard forms use the index numbers from the pattern in brackets to indicate where the word referred to in the pattern should be placed in the output phrase.

For example, consider the following row from the age dataset's phrase type sheet:

| name | pattern | valid? | standard_form |
| ---- | ------- | ------ | ------------- |
| range | `[number(0)][range_indicator(1)][number(2)][unit(3)]` | Y | `[0]-[2] [3]` |

The string "6 to 8 weeks" matches the pattern specified in this row. The `standard_form` column indicates how those elements of the pattern should be rearranged into the final string; in this case, elements 0 and 2 are the numbers "6" and "8", while element 3 is the unit "weeks". So "6 to 8 weeks" is standardized into "6-8 weeks", adopting the hyphen and spacing from the string in the `standard_form` column.
