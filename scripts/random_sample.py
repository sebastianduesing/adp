import argparse
import os
import random
import re
from converter import dict2TSV, TSV2dict


def get_error_count(line_count):
    """
    Generate the number of intentional errors to be inserted into the sample.
    """
    minimum_errors = round(line_count/100) if line_count >= 200 else 2
    maximum_errors = minimum_errors * 5
    errors = random.randint(minimum_errors, maximum_errors)
    return errors


def get_selectable_data(data, style, target_column):
    """
    Get a dict of index-row pairs for the random line selector to pick from.
    """
    selectable_data = {}
    if target_column == "location":
        output_column = "clean_output"
    else:
        output_column = f"phrase_normalized_{target_column}"
    selected_columns = {
        "index": "index",
        target_column: f"input_{style}",
        output_column: f"output_{style}"
    }
    for index, rowdict in data.items():
        selectable_line = False
        if rowdict["phrase_validation"] == "pass":
            selectable_line = True
        if "split_phrase_count" in rowdict.keys():
            if rowdict["split_phrase_count"] == "":
                selectable_line = False
            if rowdict["phrase_validity_rate"] != "1.0":
                selectable_line = False
        if rowdict["phrase_type"] == "url":
            selectable_line = False
        if selectable_line:
            selectable_data[index] = {}
            for col, pseudonym in selected_columns.items():
                selectable_data[index][pseudonym] = rowdict[col]
    return selectable_data


def pick_random_sample(selectable_data, line_count):
    """
    Select desired number of lines randomly from dict of viable lines.
    """
    index_list = [i for i in selectable_data.keys()]
    sampled_indices = random.sample(index_list, line_count)
    selected_data = {}
    for index, rowdict in selectable_data.items():
        if index in sampled_indices:
            selected_data[index] = rowdict
    return selected_data


def generate_error(data_item):
    """
    Create an intentional error in a data item string.
    """
    numbers = re.findall(r"\d+\.?\d*", data_item)
    seed = random.randint(0, 9)
    if numbers and seed > 4:
        for number in numbers:
            multiplier = random.randint(1, 100)/10
            data_item = re.sub(number, str(round(float(number)*multiplier)), data_item)
    else:
        words = re.findall(r"[a-z][a-z][a-z][a-z]+", data_item)
        word_to_scramble = random.choice(words)
        start_letter = len(word_to_scramble) - random.randint(1, (len(word_to_scramble)-1))
        first_chunk = word_to_scramble[:start_letter]
        second_chunk = word_to_scramble[start_letter:]
        scrambled_word = second_chunk + first_chunk
        data_item = re.sub(word_to_scramble, scrambled_word, data_item)
    return data_item


def insert_errors(selected_data, error_count, style):
    """
    Randomly place intentional errors in the output.
    """
    index_list = [i for i in selected_data.keys()]
    error_indices = random.sample(index_list, error_count)
    error_info = {}
    for index, rowdict in selected_data.items():
        if index in error_indices:
            output = rowdict[f"output_{style}"]
            errored_output = generate_error(output)
            if errored_output == output:
                errored_output = "error"
            rowdict[f"output_{style}"] = errored_output
            error_info[index] = {}
            error_info[index] = {
                "index": index,
                "true_input": rowdict[f"input_{style}"],
                "true_output": output,
                "errored_output": errored_output,
            }
    return selected_data, error_info


def main():
    """
    Randomly select a sample of lines and insert some random intentional errors.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", "-s", type=str,
                        help="Data style, e.g., age or data_loc")
    parser.add_argument("--column", "-c", type=str,
                        help="Name of the starting column, e.g., h_age")
    parser.add_argument("--length", "-l", type=int,
                        help="The desired line length of the sample")
    parser.add_argument("--errors", "-e", type=int,
                        help="Desired number of phony errors in the sample")
    args = parser.parse_args()
    style = args.style
    target_column = args.column
    line_count = args.length
    if args.errors:
        error_count = args.errors
    else:
        error_count = get_error_count(line_count)
    if style == "data_loc":
        infile = os.path.join(style, "output_files", f"p_norm_{style}_clean.tsv")
    else:
        infile = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    outfile = os.path.join(style, "analysis", f"random_sample_{style}.tsv")
    outdata = os.path.join(style, "analysis", f"error_key_{style}.tsv")
    data = TSV2dict(infile)
    selectable_data = get_selectable_data(data, style, target_column)
    selected_data = pick_random_sample(selectable_data, line_count)
    errored_data, error_info = insert_errors(selected_data, error_count, style)
    print(f"Generated random sample with length {line_count} and {error_count} intentional errors.")
    dict2TSV(error_info, outdata)
    dict2TSV(selected_data, outfile)


if __name__ == "__main__":
    main()
