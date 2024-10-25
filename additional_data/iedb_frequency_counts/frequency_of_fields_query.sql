-- Find which tables in which schema have an 'h_age' and 'as_location' column

-- 1. 'h_age' column
SELECT * FROM information_schema.columns WHERE column_name='h_age';

-- Go schema-by-schema and table-by-table to retrieve values and counts for:
-- Schema = [iedb_curation, iedb_production, iedb_public] & [iedb_query]
-- Tables = [bcell, mhc_elution, tcell]					  & [bcell_advanced_list, bcell_data_object, mhc_elution_advanced_list, mhc_elution_data_object, tcell_advanced_list, tcell_data_object]
SELECT h_age, COUNT(*) AS occurrences
FROM iedb_curation.mhc_elution
GROUP BY h_age
ORDER BY occurrences DESC;

-- 2. 'as_location' column
SELECT * FROM information_schema.columns WHERE column_name='as_location';

-- Go schema-by-schema and table-by-table to retrieve values and counts for:
-- Schema = [iedb_curation, iedb_production, iedb_public] & [iedb_query]
-- Tables = [bcell, mhc_bind, mhc_elution, tcell]		  & [bcell_advanced_list, bcell_data_object, mhc_elution_advanced_list, mhc_elution_data_object, tcell_advanced_list, tcell_data_object]
SELECT as_location, COUNT(*) AS occurrences
FROM iedb_production.bcell
GROUP BY as_location
ORDER BY occurrences DESC;

-- Script this: manually is too tedious
-- First for all 'h_age', get the applicable schema and tables
SELECT table_schema, table_name
FROM information_schema.columns
WHERE column_name = 'h_age' 
AND table_schema IN ('iedb_curation', 'iedb_production', 'iedb_public', 'iedb_query');

-- Step 2: Generate queries for each table found
SELECT 
    CONCAT(
        'SELECT h_age, COUNT(*) AS occurrences ',
        'FROM ', table_schema, '.', table_name, ' ',
        'GROUP BY h_age ',
        'ORDER BY occurrences DESC;'
    ) AS query_text
FROM information_schema.columns
WHERE column_name = 'h_age' 
AND table_schema IN ('iedb_curation', 'iedb_production', 'iedb_public', 'iedb_query');

-- Use the generated queries:
SELECT h_age, COUNT(*) AS occurrences FROM iedb_curation.bcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_curation.mhc_elution GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_curation.tcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_production.bcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_production.mhc_elution GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_production.tcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_public.bcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_public.mhc_elution GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_public.tcell GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.bcell_advanced_list GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.bcell_data_object GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.mhc_elution_advanced_list GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.mhc_elution_data_object GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.tcell_advanced_list GROUP BY h_age ORDER BY occurrences DESC;
SELECT h_age, COUNT(*) AS occurrences FROM iedb_query.tcell_data_object GROUP BY h_age ORDER BY occurrences DESC;

-- Now 'as_location'; get the applicable schema and tables
SELECT table_schema, table_name
FROM information_schema.columns
WHERE column_name = 'as_location' 
AND table_schema IN ('iedb_curation', 'iedb_production', 'iedb_public', 'iedb_query');

-- Step 2: Generate queries for each table found
SELECT 
    CONCAT(
        'SELECT as_location, COUNT(*) AS occurrences ',
        'FROM ', table_schema, '.', table_name, ' ',
        'GROUP BY as_location ',
        'ORDER BY occurrences DESC;'
    ) AS query_text
FROM information_schema.columns
WHERE column_name = 'as_location' 
AND table_schema IN ('iedb_curation', 'iedb_production', 'iedb_public', 'iedb_query');

-- Use the generated queries:
SELECT as_location, COUNT(*) AS occurrences FROM iedb_curation.bcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_curation.mhc_bind GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_curation.mhc_elution GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_curation.tcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_production.bcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_production.mhc_bind GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_production.mhc_elution GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_production.tcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_public.bcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_public.mhc_bind GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_public.mhc_elution GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_public.tcell GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.bcell_advanced_list GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.bcell_data_object GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.mhc_elution_advanced_list GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.mhc_elution_data_object GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.tcell_advanced_list GROUP BY as_location ORDER BY occurrences DESC;
SELECT as_location, COUNT(*) AS occurrences FROM iedb_query.tcell_data_object GROUP BY as_location ORDER BY occurrences DESC;
