"""
Script to generate a ROBOT template TSV for cell set mappings, including confidence score annotation columns after each skos:match column.

- Input: resources/scFAIR_Siletti_AT_map.tsv
- Output: src/templates/scFAIR_WHB_WMB_template.tsv
- ID: 'WHB:' + Human_cell_set_accession
- skos:exactMatch: 'WMB:' + Mouse_accession
- Score: from 'score' column, as annotation property after each match
- Ignore rows with no Mouse_accession
"""
import pandas as pd
from pathlib import Path

# File paths
input_path = Path('resources/scFAIR_Siletti_WMB_mapping/scFAIR_Siletti_AT_map.tsv')
output_path = Path('src/templates/scFAIR_WHB_WMB_template.tsv')

def main():
    # Read the input TSV
    df = pd.read_csv(input_path, sep='\t')
    
    # Filter out rows with empty Mouse_accession
    df_filtered = df[df['Mouse_accession'].notna() & (df['Mouse_accession'] != '')]
    
    # Create the output DataFrame
    output_df = pd.DataFrame()
    output_df['ID'] = 'WHB:' + df_filtered['Human_cell_set_accession'].astype(str)
    output_df['skos:exactMatch'] = 'WMB:' + df_filtered['Mouse_accession'].astype(str)
    output_df['confidence_score >A IAO:0000136'] = df_filtered['score'].astype(str)
    
    # Create header row
    header_row = pd.DataFrame([{
        'ID': 'ID',
        'skos:exactMatch': 'AI skos:exactMatch',
        'confidence_score >A IAO:0000136': 'AI IAO:0000136'
    }])
    
    # Create template row (second row)
    template_row = pd.DataFrame([{
        'ID': 'ID',
        'skos:exactMatch': 'AI skos:exactMatch',
        'confidence_score >A IAO:0000136': 'AI IAO:0000136'
    }])
    
    # Combine: header + template + data
    final_df = pd.concat([header_row, template_row, output_df], ignore_index=True)
    
    # Write to TSV
    final_df.to_csv(output_path, sep='\t', index=False, header=False)
    print(f"Generated ROBOT template: {output_path}")
    print(f"Total mappings: {len(output_df)}")

if __name__ == "__main__":
    main()
