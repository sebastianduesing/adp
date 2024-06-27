import pandas as pd
import re


def academic_location_regex():
    # Base terms for figures and tables, including common abbreviations and supplementary materials
    fig_table_terms = r"\b(table|fig(?:ure)?|(supplementary|supplemental) (?:table|fig(?:ure)|data|file?)|supporting (?:table|fig(?:ure)|information?)|additional file(s)?|appendix|suppl)\b"
    # Sections of the paper
    sections = r"\b(title|abstract|introduction|materials and methods|animals and methods|materials|methods|results|discussion|conclusion|acknowledgements|references|appendices)\b"
    # Page terms to match different ways of referencing pages
    page_terms = r"((text )?page|pg\.?|p\.?) \d+"
    # Combine them with options for numbering (e.g., figure 1, table S1)
    pattern = rf"{fig_table_terms} (?:s)?\d+[a-z]?|{sections}|{page_terms}"

    return pattern


def biological_db_regex():
    # Handle PDB identifiers, generic identifiers (letter followed by numbers), and accession numbers
    pdb_pattern = r"\bpdb [0-9][a-zA-Z0-9]{2}[a-zA-Z]|[0-9][a-zA-Z0-9][a-zA-Z][a-zA-Z0-9]|[0-9][a-zA-Z][a-zA-Z0-9]{2}\b"
    generic_identifier_pattern = r"\b[a-zA-Z] \d+\b"
    accession_pattern = r"\baccession(:)? [\w: ]+\b"
    return rf"({pdb_pattern})|({generic_identifier_pattern})|({accession_pattern})"


def website_url_regex():
    # Simple pattern for matching specific URLs and more generic HTTP URLs
    specific_domain = r"^https://hla-ligand-atlas\.org/[^\s]*$"
    general_http = r"^(https?://[^\s/$.?#].[^\s]*$)"
    return rf"({specific_domain})|({general_http})"


def is_normalized(string):
    academic_pattern = academic_location_regex()
    bio_db_pattern = biological_db_regex()
    website_pattern = website_url_regex()
        
    if re.search(academic_pattern, string, re.IGNORECASE):
        return 'Y'
    elif re.search(bio_db_pattern, string, re.IGNORECASE):
        return 'Y'
    elif re.search(website_pattern, string, re.IGNORECASE):
        return 'Y'
    else:
        return 'N'


def normalize_dataframe(df, column_name):
    # Explode the DataFrame to create a new row for each string in the list found in phrase_normalized_col
    df['normalized_location'] = df[column_name].copy()
    df = df.explode('normalized_location').reset_index(drop=True)
    df['normalized'] = df['normalized_location'].apply(is_normalized)
    return df

def dict_to_dataframe(maindict, column_name):
    # Convert dictionary to DataFrame
    df = pd.DataFrame.from_dict(maindict, orient='index')
    # Normalize data
    df = normalize_dataframe(df, column_name)
    return df

def dataframe_to_dict(df):
    # Convert DataFrame back to dictionary format suitable for dict2TSV
    result_dict = df.to_dict(orient='index')
    return result_dict
