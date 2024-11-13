import csv
import os
import sys


def sum_counts(file_list, output):
    age_sum = 0
    loc_sum = 0
    for file in file_list:
        fieldnames = None
        with open(file) as f:
            rows = csv.DictReader(f, delimiter=",")
            lines = {}
            index = 0
            for row in rows:
                if not fieldnames:
                    fieldnames = list(row.keys())
                lines[index] = row
                index += 1
        for index, row in lines.items():
            if "h_age" in row.keys():
                age_sum += int(row["occurrences"])
            if "as_location" in row.keys():
                loc_sum += int(row["occurrences"])
    with open(output, "w") as txt:
        txt.write(f"Total age values: {age_sum}\n")
        txt.write(f"Total data-location values: {loc_sum}")


def main():
    file_list = []
    directory = sys.argv[1]
    output = os.path.join(directory, "sum_data.txt")
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith("csv"):
                file_list.append(os.path.join(root, filename))
    sum_counts(file_list, output)


if __name__ == "__main__":
    main()
