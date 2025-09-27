import pandas as pd

mm_CL_mapping_Sarah = pd.read_csv(
	'./info_cell_type_complete.tsv', sep='\t')
mm_CL_mapping_Sarah_agg = mm_CL_mapping_Sarah[['cell_type',
											   'cellTypeId_',
											   'cellTypeName_']].groupby('cellTypeName_',
										 as_index=False).agg({'cell_type': list})

# Prepend 'mm_' to each cell type name
mm_CL_mapping_Sarah_agg['cellTypeName_'] = 'mm_' + mm_CL_mapping_Sarah_agg['cellTypeName_'].astype(str)

mm_CL_mapping_Sarah_agg.to_csv('WMB_set_2_CL.tsv',
							   sep='\t', index=False)


# Load the TSV file, no index_col so we can shift the first row
raw = pd.read_csv('sm_cluster.mapping_table.tsv', sep='\t', header=None)

# Shift the first row by one to the right to become the header
header = raw.iloc[0, 1:].tolist()
rows = raw.iloc[1:, 0].tolist()

# Build the square matrix DataFrame
matrix = raw.iloc[1:, 1:]
matrix.columns = header
matrix.index = rows
matrix = matrix.astype(float)

# Melt to long format
long_df = matrix.reset_index().melt(id_vars='index', var_name='c', value_name='score')
long_df = long_df.rename(columns={'index': 'r'})

# Filter out scores below 0.1
long_df = long_df[long_df['score'] >= 0.1]

# Round score to 2 decimal places and sort by score descending
long_df['score'] = long_df['score'].round(2)
long_df = long_df.sort_values(by='score', ascending=False)

# Save to new TSV
long_df.to_csv('resources/scFAIR_Siletti_WMB_mapping/sm_cluster.mappings_long.tsv', sep='\t', index=False)