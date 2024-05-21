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
    # Fill null values with 'null' string - otherwise missed in value_counts
    data = data.fillna('null')
    freq_original = data[original_col].value_counts()
    freq_phrase_normalized = data[phrase_normalized_col].value_counts()

    def create_freq_buckets(freq):
        mean = freq.mean()
        stand_dev = freq.std()
        unique = len(freq)
        single_use = (freq == 1).sum()
        single_use_percentage = (single_use / total_strings) * 100
        high_frequency = (freq >= mean + 2 * stand_dev) & (freq < mean + 3 * stand_dev)
        ultra_high_frequency = freq >= mean + 3 * stand_dev
        
        return {
            'total_strings': total_strings,
            'mean_string_frequency': mean,
            'sd_string_frequency': stand_dev,
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
    
    # Format results before filling in dictionary
    # Unique Strings
    unique_strings_change = (abs(metrics_original['unique_strings'] - metrics_phrase_normalized['unique_strings']) / metrics_original['unique_strings']) * 100
    if metrics_original['unique_strings'] > metrics_phrase_normalized['unique_strings']:
        unique_strings_change *= -1
    # Ratios of unique strings before and after phrase normalization
    ratio_value_unique_original = total_strings / metrics_original['unique_strings']
    ratio_value_unique_phrase_normalized = total_strings / metrics_phrase_normalized['unique_strings']
    unique_ratio_change = (abs(ratio_value_unique_original - ratio_value_unique_phrase_normalized) / ratio_value_unique_original) * 100
    if ratio_value_unique_original > ratio_value_unique_phrase_normalized:
        unique_ratio_change *= -1
    # Single Use Strings
    single_use_vs_all = (metrics_original['single_use'] / total_strings) * 100
    single_use_vs_unique = (metrics_original['single_use'] / metrics_original['unique_strings']) * 100
    single_use_vs_all_phrase_normalized = (metrics_phrase_normalized['single_use'] / total_strings) * 100
    single_use_vs_unique_phrase_normalized = (metrics_phrase_normalized['single_use'] / metrics_phrase_normalized['unique_strings']) * 100
    single_use_strings_change = (abs(metrics_original['single_use'] - metrics_phrase_normalized['single_use']) / metrics_original['single_use']) * 100
    if metrics_original['single_use'] > metrics_phrase_normalized['single_use']:
        single_use_strings_change *= -1
    # Ratios of 'single use' strings before and after phrase normalization
    single_use_ratio_change = (abs(single_use_vs_unique - single_use_vs_unique_phrase_normalized) / single_use_vs_unique) * 100
    if single_use_vs_unique > single_use_vs_unique_phrase_normalized:
        single_use_ratio_change *= -1
    
    
    final_results = {
        'Number of Unique Strings': metrics_original['unique_strings'],
        'Number of Unique Strings Phrase Normalized': metrics_phrase_normalized['unique_strings'],
        'Change in Number of Unique Strings': unique_strings_change,
        'Ratio of Total Strings to Unique Strings': ratio_value_unique_original,
        'Mean String Frequency': metrics_original['mean_string_frequency'],
        'Standard Deviation of String Frequency': metrics_original['sd_string_frequency'],
        'Ratio of Total Strings to Unique Strings Phrase Normalized': ratio_value_unique_phrase_normalized,
        'Mean String Frequency After Phrase Normalization': metrics_phrase_normalized['mean_string_frequency'],
        'Standard Deviation of String Frequency After Phrase Normalization': metrics_phrase_normalized['sd_string_frequency'],
        'Change in Ratio of Unique Strings to Total Strings': unique_ratio_change,
        'Number of Single Use Strings': metrics_original['single_use'],
        'Single Use Strings as a Percentage of All Strings': single_use_vs_all,
        'Single Use Strings as a Percentage of Unique Strings': single_use_vs_unique,
        'Number of Single Use Strings Phrase Normalized': metrics_phrase_normalized['single_use'],
        'Single Use Strings as a Percentage of All Strings After Phrase Normalization': single_use_vs_all_phrase_normalized,
        'Single Use Strings as a Percentage of Unique Strings After Phrase Normalization': single_use_vs_unique_phrase_normalized,
        'Change in Number of Single Use Strings': single_use_strings_change,
        'Change in Ratio of Single Use Strings to Total Strings': single_use_ratio_change
    }
    
    # Round all numeric values in the results dictionaries for better readability
    rounded_final_results = round_dict_values_in_place(final_results)
    # Format report strings (ratios)
    # Format report strings
    percentage_cols_final = ['Change in Number of Unique Strings', 'Change in Ratio of Unique Strings to Total Strings', 'Change in Number of Single Use Strings', 'Change in Ratio of Single Use Strings to Total Strings']
    for col in percentage_cols_final:
        rounded_final_results[col] = f'{rounded_final_results[col]}%'
    ratio_cols = ['Ratio of Total Strings to Unique Strings', 'Ratio of Total Strings to Unique Strings Phrase Normalized']
    for col in ratio_cols:
        rounded_final_results[col] = f'{rounded_final_results[col]} : 1'

    return rounded_final_results

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
    final_results = calculate_metrics(data, original_col)
    
    # Write final reporting result
    output_file_metrics = os.path.join(output_dir, f'{original_col}_final_results.tsv')
    write_results_to_tsv(final_results, output_file_metrics)

if __name__ == "__main__":
    main()
