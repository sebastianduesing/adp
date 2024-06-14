import random
import sys
import csv
from converter import TSV2dict, dict2TSV

def sort_dict_by_index(xdict):
    sorting_list = []
    for index, rowdict in xdict.items():
        sorting_list.append((int(rowdict["index"]), rowdict))
    sorted_list = sorted(sorting_list)
    newdict = {}
    for (index, rowdict) in sorted_list:
        newdict[index] = rowdict
    return newdict

def pick_random_lines(data, phonies, line_count):
    phony_maximum = round(0.05*len(data.keys()), 0)
    if phony_maximum > len(phonies.keys()):
        phony_maximum = len(phonies.keys())
    phony_line_count = random.randint(1, phony_maximum)
    lines_to_pull = line_count - phony_line_count
    available_indices = [index for index in data.keys()]
    sample_lines = random.sample(available_indices, k=lines_to_pull)
    for index in sample_lines:
        available_indices.remove(index)
    false_indices = random.sample(available_indices, k=phony_line_count)
    list_of_phony_indices = [index for index in phonies.keys()]
    sample_phonies = random.sample(list_of_phony_indices, k=phony_line_count)
    return sample_lines, false_indices, sample_phonies


def build_random_sheet(data, phonies, sample_lines, false_indices, sample_phonies):
    all_indices = []
    random_dict = {}
    phony_tracker = {}
    for index in sample_lines:
        all_indices.append(index)
    for index in false_indices:
        all_indices.append(index)
    for index in all_indices:
        if index in sample_lines:
            random_dict[index] = data[index]
        else:
            phony = random.choice(sample_phonies)
            random_dict[index] = phonies[phony]
            phony_tracker[index] = phonies[phony]["index"]
            random_dict[index]["index"] = index
            sample_phonies.remove(phony)
        if style == "data_loc":
            if "normalized_location" in random_dict[index].keys():
                 del random_dict[index]["normalized_location"]
            if "normalized" in random_dict[index].keys():
                del random_dict[index]["normalized"]
    random_dict = sort_dict_by_index(random_dict)
    return random_dict, phony_tracker
    

if __name__ == "__main__":
    style = sys.argv[1]
    if style == "age":
        original_col = "h_age"
    if style == "data_loc":
        original_col = "location"
    data = TSV2dict(sys.argv[2])
    line_count = int(sys.argv[3])
    phony_line_source = TSV2dict(sys.argv[4])
    output_path = sys.argv[5]
    phony_tracker_path = sys.argv[6]
    if len(data.keys()) < line_count:
        print("Error: Output line count longer than input.")
    else:
        real_lines, false_indices, phonies = pick_random_lines(data, phony_line_source, line_count)
        random_dict, phony_tracker = build_random_sheet(data, phony_line_source, real_lines, false_indices, phonies)
        dict2TSV(random_dict, output_path)
        file = open(phony_tracker_path, "w")
        file.write(f"PHONIES IN FILE {output_path}:\n")
        file.close()
        file = open(phony_tracker_path, "a")
        for sheet_index, phony_index in phony_tracker.items():
            file.write(f"Sheet index {sheet_index} = phony index {phony_index}\n")
