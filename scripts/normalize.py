# This script takes an input file and normalizes whitespace/dashes in it.

import csv
import sys


def normalize(string):
    string = string.upper().lower()
    string = string.replace(r"–", r"-")
    string = string.replace(r"—", r"-")
    return string


def main(input, output):
    with open(input, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t", restkey="errors")
        data = {}
        index = 0
        errorlist = []
        for row in reader:
            age = row["h_age"]
            id = row["h_organism_id"]
            name = row["h_organism_name"]
            data[index] = {}
            data[index]["h_age"] = age
            data[index]["h_organism_id"] = id
            data[index]["h_organism_name"] = name
            if "errors" in row.keys():
                print(f"Error: {index}")
                errorlist.append(index)
            index += 1
        if len(errorlist) == 0:
            print("No malformed lines found. Continuing...")
            for (index, row) in data.items():
                datum = row["h_age"]
                datum = normalize(datum)
                row["age_normalized"] = datum
        else:
            print("Malformed lines found. Process terminated.")
        fieldnames = ("h_age", "h_organism_id", "h_organism_name", "age_normalized")
        with open(output, "w", newline="\n") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for (index, row) in data.items():
                writer.writerow(row)
            print(f"{output} saved.")

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)
