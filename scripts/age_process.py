# This script takes an input file and a synonym reference file and outputs three files:
# "age_sorted.tsv" which contains normalizable and data of that file,
# "age_unsorted.tsv" which contains the unnormalized data, and
# "age_output.tsv" which merges the data of the previous two.
# All are ordered the same as the queried file with indices that refer to their
# line number in the input file.

import csv
import re
import sys


# compares lengths of two dicts, returning true if same and false if not
def checklength(start, end):
    print(f"Starting length: {len(start.keys())}\nResulting length: {len(end.keys())}")
    if len(start.keys()) == len(end.keys()):
        print("No lines lost!")
        return True
    else:
        print("ERROR: Starting/ending line counts don't match.")
        return False


# prints an error message if thing == false
def checkstatus(thing, process_name):
    if thing == False:
        print(f"FAILED: Could not perform {process_name}.")
        return False
    else:
        print("Continuing...")
        return True


# intakes a TSV that matches unit text to standardized units and makes a dict
def unitSynonyms(synonym_TSV):
    with open(synonym_TSV, "r", encoding="UTF-8") as infile:
        reader = csv.reader(infile, delimiter="\t")
        syndict = {}
        for text, synonym in reader:
            if synonym in syndict.keys():
                syndict[synonym].append(text)
            else:
                syndict[synonym] = [text]
        return syndict


def normalizeUnit(unit, syndict):
    normalizedUnit = unit
    for key in syndict.keys():
        if unit in syndict[key]:
            normalizedUnit = key
            break
        else:
            pass
    return normalizedUnit


# intakes TSV data, creates a dict, and adds relevant columns
def preprocess(queried_TSV):
    with open(queried_TSV, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t", restkey="errors")

        # checks for malformed lines then writes to preprocessed_dict
        index = 0
        preprocessed_dict = {}
        errorlist = []
        for row in reader:
            datum = row["h_age"]
            if "errors" in row.keys():
                print(f"Error: '{datum}'")
                errorlist.append(index)
            row["age_specified"] = ""
            row["age_minimum"] = ""
            row["age_maximum"] = ""
            row["age_unit"] = ""
            row["age_comment"] = ""
            row["index"] = index

            preprocessed_dict[index] = {}
            for i in row:
                preprocessed_dict[index][i] = row[i]

            index += 1

        if len(errorlist) != 0:
            print(
                f"ERROR: {len(errorlist)} malformed lines found, preprocessed TSV not written to dict."
            )
            print("Errors: ", errorlist)
            return False

        else:
            print("Preprocessed TSV written to dict.")
            return preprocessed_dict


regexes = [
    r"^[\.0-9]*$",
    r"^([A-Za-z\s-]+)$",
    r"^((\d+)(\.\d+)?)([\s-]*)([A-Za-z]+)(\.*)([\s-]*)(old)*$",
    r"^((\d+)(\.\d+)?)([\s-]*)to([\s-]*)((\d+)(\.\d+)?)([\s-]*)([A-Za-z]+)(\.*)([\s-]*)(old)*$",
    r"^((\d+)(\.\d+)?)([\s-]*)(to)*([\s-]*)((\d+)(\.\d+)?)$",
    r"^((\d+)(\.\d+)?)([\s-]*)((\d+)(\.\d+)?)([\s-]*)([A-Za-z]+)(\.*)([\s-]*)(old)*$",
    r"^(<|>)(\s*)((\d+)(\.\d+)?)([\s-]*)([A-Za-z]+)(\.*)([\s-]*)(old)*$",
    r"^(mean|median|average)([-:\s]*(age)*[-=\s]*)((\d+)(\.\d+)?)(([-\s]*)([A-Za-z]+)(\.*)([-\s]*)(old)*)*$",
]


# sorts dict taken from TSV into a set of dicts organized by matches to regexes
def sortByRegex(input_dict, regex_list):
    pdict = input_dict.copy()  # works on a copy interior to the function
    dictnum = 1  # tracks which dict number is being worked on
    all_dicts = {}  # stores dicts produced

    starting_length = len(pdict.keys())
    lengthsum = 0

    # make regex dicts
    for regex in regex_list:
        indextracker = []  # stores which rows have been put in the dict
        dictx = {}
        dictname = "Dict " + str(dictnum)  # names the dict to be worked on
        print(f"Creating {dictname}.")
        regex = re.compile(regex)

        for index, row in pdict.items():
            age = row["h_age"]
            m = re.match(regex, age)
            if m:
                dictx[index] = row
                indextracker.append(index)

        print(f"\t{len(dictx.keys())} lines added to {dictname}.")
        lengthsum += len(dictx.keys())
        all_dicts[dictname] = dictx
        dictnum += 1

        for i in indextracker:
            del pdict[i]

    # thinned dict is what remains after all that match a regex are removed
    print("\nCreating thinned dict.")
    all_dicts["Remainder"] = pdict
    lengthsum += len(pdict.keys())
    print(f"{len(pdict.keys())} lines added to thinned dict.")

    print(f"\nPreprocessed dict length: {starting_length}")
    print(f"All output dicts total length: {lengthsum}")

    # checks linecount of starting data with linecount of output data, fails if not the same
    if starting_length == lengthsum:
        print("No lines lost!")
        return all_dicts
    else:
        print("ERROR: Some lines missing. Dicts not returned.")
        return False


def sortAge1(dict_library):
    # r"^[\.0-9]*$"
    # pattern: only nums
    # "age_001a_numsOnly.csv"

    main = dict_library["Dict 1"]
    for i, line in main.items():
        age = line["h_age"]
        line["age_specified"] = float(age)


def sortAge2(dict_library):
    # r"^([A-Za-z\s-]+)$"
    # pattern: no nums
    # "age_002a_noNums.csv"

    main = dict_library["Dict 2"]
    for i, line in main.items():
        age = line["h_age"]
        line["age_comment"] = age


def sortAge3(dict_library, syndict):
    # (r"^((\d+)(\.\d+)?)(\s*)(-*)(\s*)([A-Za-z]+)(\s*)(-*)(\s*)(old)*$
    # pattern: num unit (old)
    # "age_003a_numberUnit.csv"

    main = dict_library["Dict 3"]
    for i, line in main.items():
        age = line["h_age"]
        ageData = re.findall(r"(\d+\.*\d*)", age)
        unitData = re.findall(r"([A-Za-z]+)", age)
        unitData = normalizeUnit(unitData[0], syndict)

        line["age_specified"] = float(ageData[0])
        line["age_unit"] = unitData


def sortAge4(dict_library, syndict):
    # r"^((\d+)(\.\d+)?)(\s*)(-*)(\s*)to(\s*)(-*)(\s*)((\d+)(\.\d+)?)(\s*)(-*)(\s*)([A-Za-z]+)(\s*)(-*)(\s*)
    # (old)*$"
    # pattern: num to num unit (old)
    # "age_004a_ageToAgeUnit.csv"

    main = dict_library["Dict 4"]
    for i, line in main.items():
        age = line["h_age"]
        ageData = re.findall(r"(\d+\.*\d*)", age)
        unitData = re.findall(r"([A-Za-z]+)", age)
        unitData = normalizeUnit(unitData[1], syndict)

        line["age_minimum"] = float(ageData[0])
        line["age_maximum"] = float(ageData[1])
        line["age_unit"] = unitData


def sortAge5(dict_library):
    # r"^((\d+)(\.\d+)?)(\s*)(-*)(\s*)((\d+)(\.\d+)?)$"
    # pattern: num-num
    # "age_005a_hyphenatedNoUnit.csv"

    main = dict_library["Dict 5"]
    for i, line in main.items():
        age = line["h_age"]
        ageData = re.findall(r"(\d+\.*\d*)", age)

        line["age_minimum"] = float(ageData[0])
        line["age_maximum"] = float(ageData[1])


def sortAge6(dict_library, syndict):
    # r"^((\d+)(\.\d+)?)(\s*)(-*)(\s*)((\d+)(\.\d+)?)(\s*)(-*)(\s*)([A-Za-z]+)(\s*)(-*)(\s*)(old)*$"
    # pattern: num-num unit (old)
    # "age_006a_hyphenatedUnit.csv"

    main = dict_library["Dict 6"]
    for i, line in main.items():
        age = line["h_age"]
        ageData = re.findall(r"(\d+\.*\d*)", age)
        unitData = re.findall(r"([A-Za-z]+)", age)
        unitData = normalizeUnit(unitData[0], syndict)

        line["age_minimum"] = float(ageData[0])
        line["age_maximum"] = float(ageData[1])
        line["age_unit"] = unitData


def sortAge7(dict_library, syndict):
    # r"^(<|>)(\s*)((\d+)(\.\d+)?)([\s-]*)([A-Za-z]+)(.*)([\s-]*)(old)*$"
    # pattern: greater/less than number unit (old)
    # "age_007a_greaterLessUnit.csv"

    main = dict_library["Dict 7"]
    for i, line in main.items():
        age = line["h_age"]
        ageData = re.findall(r"(\d+\.*\d*)", age)
        unitData = re.findall(r"([A-Za-z]+)", age)
        unitData = normalizeUnit(unitData[0], syndict)

        line["age_unit"] = unitData
        if "<" in age:
            line["age_maximum"] = float(ageData[0])
        else:
            line["age_minimum"] = float(ageData[0])


def sortAge8(dict_library, syndict):
    # r"^(mean|median|average)([-:\s]*(age)*[-=\s]*)((\d+)(\.\d+)?)(([-\s]*)([A-Za-z]+)(\.*)([-\s]*)(old)*)*$"
    # pattern: mean/median/average age number unit old
    # "age_008a_meanMedianUnit.csv"

    main = dict_library["Dict 8"]
    for i, line in main.items():
        age = line["h_age"]
        ageUnit = re.findall(r"\d+\.?\d*[-\s]*[A-Za-z]+", age)
        ageNoUnit = re.findall(r"\d+\.?\d*", age)
        textData = re.findall(r"[A-Za-z]+", age)

        line["age_comment"] = textData[0]
        if len(ageUnit) == 0:
            line["age_specified"] = float(ageNoUnit[0])
        else:
            ageData = re.findall(r"\d+\.?\d*", ageUnit[0])
            unitData = re.findall(r"[A-Za-z]+\.*", ageUnit[0])
            unitData = normalizeUnit(unitData[0], syndict)
            line["age_specified"] = float(ageData[0])
            line["age_unit"] = unitData


# performs all sortAge functions
def sortAll(dict_library, syndict):
    sortAge1(dict_library)
    sortAge2(dict_library)
    sortAge3(dict_library, syndict)
    sortAge4(dict_library, syndict)
    sortAge5(dict_library)
    sortAge6(dict_library, syndict)
    sortAge7(dict_library, syndict)
    sortAge8(dict_library, syndict)


# takes library of dicts and writes it into a single dict in order of index
def recombineDicts(dict_library, linecount):
    i = 0
    merged_dict = {}
    while i <= linecount:
        for dictx in dict_library.values():
            if i in dictx.keys():
                merged_dict[i] = dictx[i]
            else:
                pass
        i += 1
    return merged_dict


# does everything
def main(
    queried_TSV,
    regex_list,
    output_path_alldata,
    output_path_sorted,
    output_path_unsorted,
    synonym_TSV,
):
    syndict = unitSynonyms(synonym_TSV)
    preprocessed_dict = preprocess(queried_TSV)
    check = checkstatus(preprocessed_dict, "preprocessing")
    linecount = len(preprocessed_dict.keys())
    if check == False:
        print("Process has stopped.")
    else:
        dict_library = sortByRegex(preprocessed_dict, regex_list)
        check = checkstatus(dict_library, "dict sorting")
        if check == False:
            print("Process has stopped.")
        else:
            print("Organizing dicts...")
            sortAll(dict_library, syndict)
            merged_dict = recombineDicts(dict_library, linecount)
            check = checklength(preprocessed_dict, merged_dict)
            if check == False:
                print("Process has stopped.")
            else:
                with open(output_path_alldata, "w", newline="\n") as TSV:
                    fieldnames = [key for key in merged_dict[0].keys()]
                    writer = csv.DictWriter(TSV, fieldnames=fieldnames, delimiter="\t")
                    writer.writeheader()
                    for i, line in merged_dict.items():
                        writer.writerow(line)
                print(f"{output_path_alldata} has been written.")

                with open(output_path_unsorted, "w", newline="\n") as TSV:
                    fieldnames = [key for key in merged_dict[0].keys()]
                    writer = csv.DictWriter(TSV, fieldnames=fieldnames, delimiter="\t")
                    writer.writeheader()
                    for i, line in dict_library["Remainder"].items():
                        writer.writerow(line)
                print(f"{output_path_unsorted} has been written.")

                dict_library_sorted = dict_library.copy()
                del dict_library_sorted["Remainder"]
                merged_sorted = recombineDicts(dict_library_sorted, linecount)
                with open(output_path_sorted, "w", newline="\n") as TSV:
                    fieldnames = [key for key in merged_dict[0].keys()]
                    writer = csv.DictWriter(TSV, fieldnames=fieldnames, delimiter="\t")
                    writer.writeheader()
                    for i, line in merged_sorted.items():
                        writer.writerow(line)
                print(f"{output_path_sorted} has been written.")

                print("\nCompleted successfully!")


if __name__ == "__main__":
    input_file = sys.argv[1]
    synonyms = sys.argv[2]
    all_out = sys.argv[3]
    sorted_out = sys.argv[4]
    unsorted_out = sys.argv[5]
    main(
        input_file,
        regexes,
        all_out,
        sorted_out,
        unsorted_out,
        synonyms,
        )
