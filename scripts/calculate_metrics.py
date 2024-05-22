import pandas as pd
import sys
import os
import warnings
import ast

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
        return pd.read_csv(file_path, sep='\t', dtype=str, encoding='utf-8')
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

def write_results_to_tsv(results, output_file):
    """
    Write results to a TSV file.
    """
    results_df = pd.DataFrame(list(results.items()), columns=['Metric', 'Value'])
    results_df.to_csv(output_file, index=False, sep='\t', encoding='utf-8')
    print(f"Results written to {output_file}")

def create_freq_buckets(data, col):
    """
    Calculate frequency metrics for a given column in a DataFrame.

    Parameters:
    - data (DataFrame): The input DataFrame.
    - col (str): The name of the column to calculate metrics for.

    Returns:
    - dict: A dictionary containing the calculated metrics:
        - total_strings (int): The total number of strings in the column.
        - mean_string_frequency (float): The mean frequency of strings in the column.
        - sd_string_frequency (float): The standard deviation of string frequency in the column.
        - unique_strings (int): The number of unique strings in the column.
        - single_use (int): The number of strings that appear only once in the column.
        - mid_frequency (int): The number of strings with frequency greater than 1 SD & less than 3 SD from the mean.
        - high_frequency (int): The number of strings with frequency greater than or equal to 3 SD from the mean.
        - unique_percentage (float): The percentage of unique strings in the column.
        - single_use_percentage (float): The percentage of strings that appear only once in the column.
        - mid_frequency_percentage (float): The percentage of strings with frequency greater than 1 SD & less than 3 SD from the mean.
        - high_frequency_percentage (float): The percentage of strings with frequency greater than or equal to 3 SD from the mean.
    """
    # Count the frequency of each string in the column
    freq = data[col].value_counts()
    
    # Calculate metrics for the frequency distribution
    total_strings = len(data)
    mean = freq.mean()
    stand_dev = freq.std()
    unique = len(freq)
    single_use = (freq == 1).sum()
    single_use_percentage = (single_use / total_strings) * 100
    mid_frequency = (freq > (mean + stand_dev)) & (freq < (mean + (3 * stand_dev)))
    high_frequency = freq >= (mean + (3 * stand_dev))
    
    # Return the metrics as a dictionary
    return {
        'total_strings': total_strings,
        'mean_string_frequency': mean,
        'sd_string_frequency': stand_dev,
        'unique_strings': unique,
        'single_use': single_use,
        'mid_frequency': mid_frequency.sum(),
        'high_frequency': high_frequency.sum(),
        'unique_percentage': (unique / total_strings) * 100,
        'single_use_percentage': single_use_percentage,
        'mid_frequency_percentage': (mid_frequency.sum() / total_strings) * 100,
        'high_frequency_percentage': (high_frequency.sum() / total_strings) * 100
    }

def calculate_metrics(input_file, data, original_col):
    """
    Calculate various metrics including unique strings, frequency distributions,
    and percentages as specified in the manuscript.
    """
    # Define the phrase-normalized column name
    phrase_normalized_col = f'phrase_normalized_{original_col}'
    
    # This only pertains to data location field - stored lists in the phrase column
    if original_col == 'location':
        # Check if we've used N/A to exclude known invalid locations; if so, remove rows with N/A
        data = data[~data[phrase_normalized_col].apply(lambda x: 'N/A' in x)].copy()

        # Expand lists in the phrase column to separate rows
        #if phrase_normalized_col in data.columns:
        #    data[phrase_normalized_col] = data[phrase_normalized_col].apply(parse_possible_list)
        #    data = data.explode(phrase_normalized_col)
        #    data = data.reset_index(drop=True)
        
        # Save the exploded data to a new TSV file
        #exploded_file = input_file.replace('.tsv', '_exploded.tsv')
        #print(f"Saving exploded data to {exploded_file}")
        #data.to_csv(exploded_file, index=False, sep='\t', encoding='utf-8')
        
        # Define the normalized location column name
        norm_loc_col = f'normalized_{original_col}'
        
        # Find the strings that appear only once in the norm_loc_col column...
        is_unique_in_loc_norm_strings = data[norm_loc_col].map(data[norm_loc_col].value_counts()) == 1
        # ...'N' for normalized...
        is_N_in_norm = data['normalized'] == 'N'
        # ...is not numeric...
        not_numeric = ~(data[norm_loc_col].astype(str).str.isnumeric().fillna(False))
        # ...and combine the conditions to get the unique strings that are unnormalized
        unique_N_str = data[is_unique_in_loc_norm_strings & is_N_in_norm & not_numeric]

        # Save the unique strings for manual review        
        manual_review_file = input_file.replace('.tsv', '_manual_review.tsv')
        print(f"Saving strings for manual review to {manual_review_file}")
        unique_N_str[norm_loc_col].to_csv(manual_review_file, index=False, sep='\t', encoding='utf-8')

    # Fill null values with 'null' string - otherwise missed in value_counts
    data = data.fillna('null')

    # Create metrics dictionaries for original and phrase-normalized columns
    metrics_original = create_freq_buckets(data, original_col)
    metrics_phrase_normalized = create_freq_buckets(data, phrase_normalized_col)
    
    # Format results before filling in dictionary following manuscript metrics
    # Unique Strings
    unique_strings_change = (abs(metrics_original['unique_strings'] - metrics_phrase_normalized['unique_strings']) / metrics_original['unique_strings']) * 100
    if metrics_original['unique_strings'] > metrics_phrase_normalized['unique_strings']:
        unique_strings_change *= -1
    # Ratios of unique strings before and after phrase normalization
    total_strings = len(data)
    ratio_value_unique_original = total_strings / metrics_original['unique_strings']
    ratio_value_unique_phrase_normalized = total_strings / metrics_phrase_normalized['unique_strings']
    unique_ratio_change = (abs(ratio_value_unique_original - ratio_value_unique_phrase_normalized) / ratio_value_unique_original) * 100
    if ratio_value_unique_original > ratio_value_unique_phrase_normalized:
        unique_ratio_change *= -1
    # 'Single Use' Strings
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
        'Number of Unique Strings After Phrase Normalization': metrics_phrase_normalized['unique_strings'],
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
        'Change in Ratio of Single Use Strings to Total Strings': single_use_ratio_change,
        'Mid Frequency Strings': metrics_original['mid_frequency'],
        'Mid Frequency Strings as a Percentage of All Strings': metrics_original['mid_frequency_percentage'],
        'Mid Frequency Strings After Phrase Normalization': metrics_phrase_normalized['mid_frequency'],
        'Mid Frequency Strings as a Percentage of All Strings After Phrase Normalization': metrics_phrase_normalized['mid_frequency_percentage'],
        'High Frequency Strings': metrics_original['high_frequency'],
        'High Frequency Strings as a Percentage of All Strings': metrics_original['high_frequency_percentage'],
        'High Frequency Strings After Phrase Normalization': metrics_phrase_normalized['high_frequency'],
        'High Frequency Strings as a Percentage of All Strings After Phrase Normalization': metrics_phrase_normalized['high_frequency_percentage']
    }
    
    # Round all numeric values in the results dictionaries for better readability
    rounded_final_results = round_dict_values_in_place(final_results)
    # Format report strings (percentages)
    percentage_cols_final = ['Change in Number of Unique Strings', 'Change in Ratio of Unique Strings to Total Strings', 'Change in Number of Single Use Strings', 'Change in Ratio of Single Use Strings to Total Strings']
    for col in percentage_cols_final:
        rounded_final_results[col] = f'{rounded_final_results[col]}%'
    # Format report strings (ratios)
    ratio_cols = ['Ratio of Total Strings to Unique Strings', 'Ratio of Total Strings to Unique Strings Phrase Normalized']
    for col in ratio_cols:
        rounded_final_results[col] = f'{rounded_final_results[col]} : 1'

    return rounded_final_results

def main():
    """
    Main function to load data, calculate metrics, and write results to TSV files.
    """
    if len(sys.argv) < 4:
        print("Usage: python calculate_metrics.py <tsv_file_path> <original_column_name> <output_directory_path>")
        sys.exit(1)

    input_file = sys.argv[1]
    original_col = sys.argv[2]
    output_dir = sys.argv[3]

    data = load_data(input_file)
    final_results = calculate_metrics(input_file, data, original_col)
    
    # Write final reporting result
    output_file = os.path.join(output_dir, f'{original_col}_final_results.tsv')
    write_results_to_tsv(final_results, output_file)

if __name__ == "__main__":
    main()
