import sys
import os
import warnings
import ast
import math
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Removing deprecation warning
warnings.filterwarnings("ignore", category=Warning, module="pandas")

# Define some printable values
printable_style = {'age': 'Age Dataset', 'data_loc': 'Data Location Dataset'}

def round_to_nearest_sig(x):
    """
    Rounds a number to the nearest significant figure.

    Args:
        x (float): The number to be rounded.

    Returns:
        float: The rounded number.

    Examples:
        >>> round_to_nearest_sig(1234)
        1000
        >>> round_to_nearest_sig(0.00567)
        0.01
    """
    if x == 0:
        return 0
    else:
        # Determine the order of magnitude of the number
        order_of_magnitude = math.floor(math.log10(abs(x)))
        # Calculate the rounding factor as 10 raised to the order of magnitude
        rounding_factor = 10 ** order_of_magnitude
        # Round the number to the nearest significant figure
        return round(x / rounding_factor) * rounding_factor

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
    low_frequency = (freq > 1) & (freq <= (mean + stand_dev))
    mid_frequency = (freq > (mean + stand_dev)) & (freq < (mean + (3 * stand_dev)))
    high_frequency = freq >= (mean + (3 * stand_dev))
    
    # Return the metrics as a dictionary
    return {
        'total_strings': total_strings,
        'mean_string_frequency': mean,
        'sd_string_frequency': stand_dev,
        'unique_strings': unique,
        'single_use': single_use,
        'low_frequency': low_frequency.sum(),
        'mid_frequency': mid_frequency.sum(),
        'high_frequency': high_frequency.sum(),
        'unique_percentage': (unique / total_strings) * 100,
        'single_use_percentage': single_use_percentage,
        'low_frequency_percentage': (low_frequency.sum() / total_strings) * 100,
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
        
        # Define the normalized location column name
        norm_loc_col = f'phrase_normalized_{original_col}'
        
        # Find the strings that appear only once in the norm_loc_col column...
        is_unique_in_loc_norm_strings = data[norm_loc_col].map(data[norm_loc_col].value_counts()) == 1
        # ...'fail' for normalized...
        is_N_in_norm = data['phrase_validation'] == 'fail'
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
        'Low Frequency Strings': metrics_original['low_frequency'],
        'Low Frequency Strings as a Percentage of All Strings': metrics_original['low_frequency_percentage'],
        'Low Frequency Strings After Phrase Normalization': metrics_phrase_normalized['low_frequency'],
        'Low Frequency Strings as a Percentage of All Strings After Phrase Normalization': metrics_phrase_normalized['low_frequency_percentage'],
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
    percentage_cols_final = ['Change in Number of Unique Strings', 'Change in Ratio of Unique Strings to Total Strings', 'Change in Number of Single Use Strings', 'Change in Ratio of Single Use Strings to Total Strings', 'Single Use Strings as a Percentage of All Strings', 'Single Use Strings as a Percentage of Unique Strings', 'Single Use Strings as a Percentage of All Strings After Phrase Normalization', 'Single Use Strings as a Percentage of Unique Strings After Phrase Normalization', 'Low Frequency Strings as a Percentage of All Strings', 'Low Frequency Strings as a Percentage of All Strings After Phrase Normalization', 'Mid Frequency Strings as a Percentage of All Strings', 'Mid Frequency Strings as a Percentage of All Strings After Phrase Normalization', 'High Frequency Strings as a Percentage of All Strings', 'High Frequency Strings as a Percentage of All Strings After Phrase Normalization']
    for col in percentage_cols_final:
        rounded_final_results[col] = f'{rounded_final_results[col]}%'
    # Format report strings (ratios)
    ratio_cols = ['Ratio of Total Strings to Unique Strings', 'Ratio of Total Strings to Unique Strings Phrase Normalized']
    for col in ratio_cols:
        rounded_final_results[col] = f'{rounded_final_results[col]} : 1'

    return rounded_final_results

def generate_freq_distribution_figures(results, output_file, type):
    """
    Generate frequency distribution figures based on the results dataframe.

    Parameters:
    - results (DataFrame): The results dataframe containing the frequency distribution data.
    - output_file (str): The file path to save the generated figure.
    - type (str): The type of data frequency.

    Returns:
    None
    """
    # Extract the relevant columns from the results dataframe
    original_keys = ['Number of Single Use Strings', 'Low Frequency Strings', 'Mid Frequency Strings', 'High Frequency Strings']
    original_values = list(map(results.get, original_keys))
    normalized_keys = ['Number of Single Use Strings Phrase Normalized', 'Low Frequency Strings After Phrase Normalization', 'Mid Frequency Strings After Phrase Normalization', 'High Frequency Strings After Phrase Normalization']
    normalized_values = list(map(results.get, normalized_keys))
    max_values = max(original_values), max(normalized_values)
    offset = round_to_nearest_sig(int(max(max_values) * 0.25))
    
    # Set the x-axis labels
    x_labels = ['Single Use', 'Low Frequency', 'Mid Frequency', 'High Frequency']
    
    # Set the bar width
    bar_width = 0.35
    
    # Set the positions of the bars on the x-axis
    r1 = range(len(x_labels))
    r2 = [x + bar_width for x in r1]
    
    # Plot the original values
    bars1 = plt.bar(r1, original_values, color='g', width=bar_width, label=f'{type} (Pre-Normalization)')
    
    # Plot the normalized values
    bars2 = plt.bar(r2, normalized_values, color='b', width=bar_width, label=f'{type} (Post-Normalization)')
    
    # Adding the text labels on the bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height, '%d' % int(height), ha='center', va='bottom')

    add_labels(bars1)
    add_labels(bars2)

    # Customize the plot
    plt.ylabel(f'# of {type}')
    plt.title(f'{type} by Data Frequency Type')
    plt.xticks([r + bar_width/2 for r in range(len(x_labels))], x_labels)
    plt.yticks(range(0, max(max(original_values), max(normalized_values)) + offset, offset))
    plt.grid(True, which='major', linestyle='--', linewidth='0.5', color='grey', axis='y')
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)

    # Reposition the legend
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)

    # Save the plot to the output file
    plt.savefig(output_file)

def generate_normalization_phase_figure(df, style, output_file):
    """
    Generate a bar chart showing the counts of altered and unaltered rows for each normalization phase.

    Args:
        df (pandas.DataFrame): The input DataFrame containing the data.
        style (str): The style of the dataset ('age' or 'data_loc').
        output_file (str): The path to save the output file.

    Returns:
        None
    """
    # Counting occurrences of 'pass' and 'fail' for each normalization step
    count_char = df['char_validation'].value_counts()
    count_word = df['word_validation'].value_counts()
    count_phrase = df['phrase_validation'].value_counts()
    
    # Prepare counts for the chart
    altered_counts = [count_char.get('pass', 0), count_word.get('pass', 0), count_phrase.get('pass', 0)]
    unaltered_counts = [count_char.get('fail', 0), count_word.get('fail', 0), count_phrase.get('fail', 0)]
    max_counts = [max(altered_counts), max(unaltered_counts)]
    offset = round_to_nearest_sig(int(max(max_counts) * 0.25))
    
    # Create the DataFrame for counts
    counts_df = pd.DataFrame({
        'Altered': altered_counts,
        'Unaltered': unaltered_counts
    }, index=['Character', 'Word', 'Phrase'])
    
    # Plotting the data
    if style == 'age':
        style_str = 'Age Dataset'
    elif style == 'data_loc':
        style_str = 'Data Location Dataset'
    ax = counts_df.plot(kind='bar', color=['blue', 'orange'], figsize=(8, 6))
    ax.set_title(f'{style_str}: Rows Altered by Normalization Phase')
    ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.01), frameon=False)
    plt.grid(True, which='major', linestyle='--', linewidth='0.5', color='grey', axis='y')
    plt.xticks(rotation=0)
    plt.yticks(range(0, max(max_counts) + offset, offset))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Save the plot to the output file
    plt.savefig(output_file)

def generate_unique_string_figures(data, output_file, style):
    pre_norm_unique = data["Number of Unique Strings"]
    post_norm_unique = data["Number of Unique Strings After Phrase Normalization"]
    dataset = pd.DataFrame(
                           [
                               {"Pre-Normalization": pre_norm_unique,
                               "Post-Normalization": post_norm_unique}
                           ],
                           index=["Pre- vs Post-Normalization"])
    if style == "age":
        style_str = "Age"
    elif style == "data_loc":
        style_str = "Data-Location"
    ax = dataset.plot(kind="bar", color=["blue", "orange"], figsize=(8,6))
    ax.set_title(f"{style_str}: # of Unique Strings Before & After Normalization")
    plt.grid(True, which="major", linestyle="--", linewidth="0.5", color="grey", axis="y")
    plt.xticks(rotation=0)
    plt.savefig(output_file)

def plot_scatter_phrase_count_vs_validity(data, style, exclude_urls=False):
    '''
    Scatter plot of split phrase count vs. phrase validity rate.
    Optionally excludes URL data items.
    '''
    if exclude_urls:
        data = data[(data['split_phrase_count'] != 1) | (data['phrase_validity_rate'] != 1)]
    
    # Group data to count occurrences of each (split_phrase_count, phrase_validity_rate) pair
    data_grouped = data.groupby(['split_phrase_count', 'phrase_validity_rate']).size().reset_index(name='count')

    # Adjust point sizes based on the count
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x='split_phrase_count', 
        y='phrase_validity_rate', 
        size='count', 
        sizes=(20, 2000),  # Adjust the min and max size to fit the plot well
        data=data_grouped, 
        legend=False
    )
    
    printable_style = {'age': 'Age Dataset', 'data_loc': 'Data Location Dataset'}
    
    plt.title(f'Split Phrase Count vs. Validity Rate - {printable_style[style]}{" (Excl. URLs)" if exclude_urls else ""}')
    plt.xlabel('Split Phrase Count')
    plt.ylabel('Phrase Validity Rate')
    plt.grid(True)
    plt.savefig(f'{style}/analysis/figures/scatter_count_vs_validity{"_no_urls" if exclude_urls else ""}.png')
    plt.close()

def plot_validation_pie_charts(data, style):
    '''
    Pie charts for validation pass/fail/stopped rates at each stage (char, word, phrase).
    '''
    stages = ['char_validation', 'word_validation', 'phrase_validation']
    stage_labels = ['Character Stage', 'Word Stage', 'Phrase Stage']
    stage_percents = [data[stage].value_counts(normalize=True) * 100 for stage in stages]
    printable_style = {'age': 'Age Dataset', 'data_loc': 'Data Location Dataset'}

    # Create pie charts for each stage
    for stage, label, stage_percent in zip(stages, stage_labels, stage_percents):
        counts = data[stage].value_counts()
        # Create formatted labels for the current stage
        labels = [f'{label} - {value}: {percent:.2f}%' for value, percent in stage_percent.items()]
        
        plt.figure(figsize=(6, 6))
        wedges, texts = plt.pie(counts,
                                startangle=90,
                                wedgeprops = {"edgecolor" : "black", 'linewidth': 0.2, 'antialiased': True})
        
        plt.title(f'Validation Results - {label} - {printable_style[style]}')
        plt.legend(wedges, labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), fontsize=8)
        
        plt.savefig(f'{style}/analysis/figures/validation_pie_{stage}.png')
        plt.close()

# Updated function to create two versions of histograms: one with log-scaled y-axis and one without
def plot_levenshtein_histogram(data, style):
    '''
    Histogram of Levenshtein distance scores at character and word stages.
    '''
    stages = ['char_distance_score', 'word_distance_score']
    labels = ['Character Stage', 'Word Stage']
    output_file_normal = f'{style}/analysis/figures/levenshtein_hist_{{}}.png'
    output_file_log = f'{style}/analysis/figures/levenshtein_hist_{{}}_log.png'

    for stage, label in zip(stages, labels):
        # Plot histogram with normal y-axis
        plt.figure(figsize=(10, 6))
        sns.histplot(data[stage], binwidth=1, kde=False, edgecolor='black', linewidth=0.5)
        plt.title(f'Levenshtein Distance Frequency - {label} - {printable_style[style]} (Normal Scale)')
        plt.xlabel('Levenshtein Distance')
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.xticks(range(int(data[stage].min()), int(data[stage].max()) + 1))
        plt.savefig(output_file_normal.format(stage), bbox_inches='tight')
        plt.close()

        # Plot histogram with log-scaled y-axis
        plt.figure(figsize=(10, 6))
        sns.histplot(data[stage], binwidth=1, kde=False, edgecolor='black', linewidth=0.5)
        plt.title(f'Levenshtein Distance Frequency - {label} - {printable_style[style]} (Log Scale)')
        plt.xlabel('Levenshtein Distance')
        plt.ylabel('Frequency (Log Scale)')
        plt.yscale('log')
        plt.grid(True, which="both", linestyle='--', linewidth=0.5)
        plt.xticks(range(int(data[stage].min()), int(data[stage].max()) + 1))
        plt.savefig(output_file_log.format(stage), bbox_inches='tight')
        plt.close()

    print(f"Levenshtein distance histograms saved to {output_file_normal.format('char')}, {output_file_log.format('char')}, "
          f"{output_file_normal.format('word')}, and {output_file_log.format('word')}")

# Updated function to adjust spacing and reformat subplot labels
def plot_combined_validation_pie_charts(data, style):
    """
    Create a single figure with three pie charts for character, word, and phrase validation results.
    """
    validations = {
        "Character Validation": "char_validation",
        "Word Validation": "word_validation",
        "Phrase Validation": "phrase_validation"
    }

    # Create a figure with three subplots (1 row, 3 columns)
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))  # Increased figure size to prevent cropping

    labels = ['a', 'b', 'c']

    for ax, (label, (title, column)) in zip(axes, zip(labels, validations.items())):
        # Get counts for "pass" and "fail" (combine "stopped" and "fail" as "fail")
        counts = data[column].replace({"stopped": "fail", "fail": "fail"}).value_counts()

        # Reindex to ensure both "pass" and "fail" are present, fill missing with 0
        counts = counts.reindex(["pass", "fail"], fill_value=0)

        # Plot pie chart
        ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#F44336'], textprops={'fontsize': 18})
        ax.set_title(title, fontsize=24, pad=10)  # Keep subtitle centered and add padding

        # Add subplot label in the top left corner
        ax.text(-1.6, 1.5, f"{label})", fontsize=24, fontweight='bold', va='top', ha='left')

    # Adjust layout to reduce space between the main title and the individual subplots
    plt.subplots_adjust(top=0.85, wspace=0.3, hspace=0.1)
    plt.suptitle(f"Validation Results - {printable_style[style]}", fontsize=28, y=0.92)

    # Save the combined figure in the output directory
    output_file = f"{style}/analysis/figures/{style}_combined_validation_pie_charts.png"
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()

    print(f"Combined validation pie charts saved to {output_file}")

def generate_additional_figures(input_file, style):
    '''
    Generates additional figures based on the dataset style.
    '''
    data = pd.read_csv(input_file, sep='\t')

    # Generate scatter plots for data location datasets "split_phrase_count" vs. "phrase_validity_rate"
    if style == 'data_loc':
        plot_scatter_phrase_count_vs_validity(data, style)
        plot_scatter_phrase_count_vs_validity(data, style, exclude_urls=True)

    # Generate validation pie chart
    plot_combined_validation_pie_charts(data, style)

    # Generate Levenshtein distance histograms
    plot_levenshtein_histogram(data, style)

def main():
    """
    Main function to load data, calculate metrics, and write results to TSV files.
    """
    if len(sys.argv) < 5:
        print("Usage: python calculate_metrics.py <tsv_file_path> <original_column_name> <output_directory_path> <style>")
        sys.exit(1)

    style = sys.argv[4]
    input_file = os.path.join(style, sys.argv[1])
    original_col = sys.argv[2]
    output_dir = os.path.join(style, sys.argv[3])

    data = load_data(input_file)
    final_results = calculate_metrics(input_file, data, original_col)
    
    # Write final reporting result
    output_file = os.path.join(output_dir, f'{original_col}_final_results.tsv')
    write_results_to_tsv(final_results, output_file)

# Commented out some function calls for figures we don't use currently
    
    # Generate frequency distribution figures
    # TODO: Discuss the "Rows" with Sebastian
#    for type in ["Data Items"]:#, "Rows"]:
#        type_str = type.lower().replace(' ', '_')
#        output_fig = os.path.join(output_dir, f'{style}_frequency_distribution_{type_str}.png')
#        generate_freq_distribution_figures(final_results, output_fig, type)
    
    # Generate normalization phase figure
#    output_file = os.path.join(output_dir, f'{style}_normalization_phase.png')
#    generate_normalization_phase_figure(data, style, output_file)

    # Generate unique string figures
#    output_file = os.path.join(output_dir, f"{style}_unique_strings.png")
#    generate_unique_string_figures(final_results, output_file, style)
    
    # Generate the three additional figures: scatter plots, validation pie charts, and Levenshtein histograms
    generate_additional_figures(input_file, style)

if __name__ == "__main__":
    main()
