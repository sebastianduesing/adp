import argparse
import os
from converter import TSV2dict, dict2TSV
from statistics import mean, median, stdev


def numberize(numstring):
    other_chars = False
    for char in numstring:
        if char not in "0123456789.":
            other_chars = True
    if other_chars:
        return None
    else:
        if "." in numstring:
            return float(numstring)
        else:
            return int(numstring)


def add_metric(metrics, name, value):
    if len(metrics.keys()) == 0:
        new_index = 0
    else:
        indices = [i for i in metrics.keys()]
        largest_index = indices[-1]
        new_index = largest_index + 1
    metrics[new_index] = {
        "metric": name,
        "value": value,
    }


def get_basic_metrics(style, data, target_column, metrics):
    cols = {
        "char_validation": "Character stage validation pass rate",
        "char_distance_score": "Character stage Levenshtein distance score",
        "word_validation": "Word stage validation pass rate",
        "word_distance_score": "Word stage Levenshtein distance score",
        "phrase_validation": "Phrase stage validation pass rate",
    }
    for col in ["char_validation", "word_validation", "phrase_validation"]:
        tracker = {}
        for index, rowdict in data.items():
            if rowdict[col] != "":
                if rowdict[col] not in tracker.keys():
                    tracker[rowdict[col]] = 1
                else:
                    count = tracker[rowdict[col]]
                    count += 1
                    tracker[rowdict[col]] = count
        total = 0
        for value, count in tracker.items():
            total += count
        pass_count = tracker["pass"] if "pass" in tracker.keys() else 0
        rate = round(pass_count/total, 4)
        add_metric(metrics, cols[col], rate)
    for col in [
        "char_distance_score",
        "word_distance_score",
    ]:
        tracker = []
        for index, rowdict in data.items():
            if rowdict[col] != "":
                tracker.append(numberize(rowdict[col]))
        col_median = median(tracker)
        col_mean = round(mean(tracker), 4)
        col_stdev = round(stdev(tracker), 4)
        add_metric(metrics, f"{cols[col]} median", col_median)
        add_metric(metrics, f"{cols[col]} mean", col_mean)
        add_metric(metrics, f"{cols[col]} standard deviation", col_stdev)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", "-s",
                        help="Data style, e.g., age or data_loc")
    parser.add_argument("--filename", "-f",
                        help="Target filename, if not p_norm_<style>.tsv")
    parser.add_argument("--column", "-c",
                        help="Name of the starting column, e.g., h_age")
    args = parser.parse_args()
    style = args.style
    path = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    if args.filename:
        path = os.path.join(style, "output_files", args.filename)
    output = os.path.join(style, "output_files", f"{style}_basic_metrics.tsv")
    target_column = args.column
    data = TSV2dict(path)
    metrics = {}
    get_basic_metrics(style, data, target_column, metrics)
    dict2TSV(metrics, output)


if __name__ == "__main__":
    main()
