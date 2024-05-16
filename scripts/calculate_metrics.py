import pandas as pd
import sys
import os
import warnings
import ast  # Import ast library to safely evaluate strings that look like Python lists

# Removing deprecation warning
warnings.filterwarnings("ignore", category=Warning, module="pandas")

def round_dict_values_in_place(d, decimals=2):
    """
    Round all numeric values in a dictionary to a specified number of decimal places.
    """
    for k, v in list(d.items()):  # Convert to list to safely modify the dictionary during iteration.
        try:
            if isinstance(v, (int, float)):  # Check if the value is a number
                d[k] = round(v, decimals)
            # If the value is not a number, it remains unchanged
        except TypeError as e:
            return f"Error rounding value {v} for key {k}: {e}"
    return d

def load_data(file_path):
    """
    Load data from a TSV file into a pandas DataFrame.
    """
    try:
        return pd.read_csv(file_path, sep='\t')
    except Exception as e:
        print(f"Failed to load data: {e}")
        sys.exit(1)

def parse_possible_list(s):
    """
    Parse the string as a list if it's formatted as one.
    """
    try:
        if s.startswith('[') and s.endswith(']'):
            return ast.literal_eval(s)  # Safely evaluate the string as a Python literal
        return [s]  # Return a list containing the string itself if not a list format
    except:
        return [s]  # In case of any error during parsing, treat it as a simple string

def calculate_metrics(data, original_col):
    """
    Calculate various metrics including unique strings, frequency distributions,
    and percentages as specified in the prompt.
    """
    phrase_normalized_col = f'phrase_normalized_{original_col}'

    # Find number of original strings
    initial_string_count = len(data)

    # Preprocess phrase_normalized column by parsing lists
    if phrase_normalized_col in data.columns:
        data[phrase_normalized_col] = data[phrase_normalized_col].apply(parse_possible_list)
        data = data.explode(phrase_normalized_col)  # This will duplicate rows based on list length

    total_strings = len(data)
    freq_original = data[original_col].value_counts()
    freq_phrase_normalized = data[phrase_normalized_col].value_counts()

    def create_freq_buckets(freq):
        mean = freq.mean()
        std = freq.std()
        unique = freq.nunique()
        single_use = (freq == 1).sum()
        single_use_percentage = (single_use / total_strings) * 100
        high_frequency = (freq >= mean + 2 * std) & (freq < mean + 3 * std)
        ultra_high_frequency = freq >= mean + 3 * std
        
        return {
            'total_strings': total_strings,
            'unique_strings': unique,
            'single_use': single_use,
            'high_frequency': high_frequency.sum(),
            'ultra_high_frequency': ultra_high_frequency.sum(),
            'unique_percentage': (unique / total_strings) * 100,
            'single_use_percentage': single_use_percentage,
            'high_frequency_percentage': (high_frequency.sum() / total_strings) * 100,
            'ultra_high_frequency_percentage': (ultra_high_frequency.sum() / total_strings) * 100
        }

    metrics_original = create_freq_buckets(freq_original)
    metrics_phrase_normalized = create_freq_buckets(freq_phrase_normalized)

    counts_results = {
        'Total Strings': total_strings,
        'Unique Strings Original': metrics_original['unique_strings'],
        'Unique Strings Phrase Normalized': metrics_phrase_normalized['unique_strings'],
        'Single Use Original': metrics_original['single_use'],
        'Single Use Phrase Normalized': metrics_phrase_normalized['single_use'],
        'High Frequency Original': metrics_original['high_frequency'],
        'High Frequency Phrase Normalized': metrics_phrase_normalized['high_frequency'],
        'Ultra High Frequency Original': metrics_original['ultra_high_frequency'],
        'Ultra High Frequency Phrase Normalized': metrics_phrase_normalized['ultra_high_frequency']
    }

    percentages_results = {
        'Total Strings Percentage': (total_strings / initial_string_count) * 100,
        'Unique Strings Original Percentage': metrics_original['unique_percentage'],
        'Unique Strings Phrase Normalized Percentage': metrics_phrase_normalized['unique_percentage'],
        'Single Use Original Percentage': metrics_original['single_use_percentage'],
        'Single Use Phrase Normalized Percentage': metrics_phrase_normalized['single_use_percentage'],
        'High Frequency Original Percentage': metrics_original['high_frequency_percentage'],
        'High Frequency Phrase Normalized Percentage': metrics_phrase_normalized['high_frequency_percentage'],
        'Ultra High Frequency Original Percentage': metrics_original['ultra_high_frequency_percentage'],
        'Ultra High Frequency Phrase Normalized Percentage': metrics_phrase_normalized['ultra_high_frequency_percentage']
    }
    
    # Round all numeric values in the results dictionaries for better readability
    rounded_counts_results = round_dict_values_in_place(counts_results)
    rounded_percentages_results = round_dict_values_in_place(percentages_results)

    return rounded_counts_results, rounded_percentages_results

def write_results_to_tsv(results, output_file):
    """
    Write results to a TSV file.
    """
    results_df = pd.DataFrame(list(results.items()), columns=['Metric', 'Value'])
    results_df.to_csv(output_file, index=False, sep='\t', encoding='utf-8')
    print(f"Results written to {output_file}")

def main():
    """
    Main function to load data, calculate metrics, and write results to TSV files.
    """
    if len(sys.argv) < 4:
        print("Usage: python calculate_metrics.py <tsv_file_path> <original_column_name> <output_directory_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    original_col = sys.argv[2]
    output_dir = sys.argv[3]

    data = load_data(file_path)
    counts_results, percentages_results = calculate_metrics(data, original_col)

    # Write counts results
    output_file_counts = os.path.join(output_dir, f'{original_col}_counts_results.tsv')
    write_results_to_tsv(counts_results, output_file_counts)

    # Write percentages results
    output_file_metrics = os.path.join(output_dir, f'{original_col}_metrics_results.tsv')
    write_results_to_tsv(percentages_results, output_file_metrics)

if __name__ == "__main__":
    main()
