import requests
import json
import pandas as pd

wmb = requests.get("https://github.com/brain-bican/whole_mouse_brain_taxonomy/raw/refs/heads/main/CCN20230722.json")
wmb_json = wmb.text
wmb_data = json.loads(wmb_json)

WMB_AT = pd.read_csv('resources/BG_2_WMB_curated_MMC_mappings.csv',
                      sep=',').dropna(how='all')

## Columns 'curated_ABC_WMB_supertype' and 'curated_ABC_WMB_cluster' contain the labels of transferred WMB terms
## WHere there are multiples they are separated by ' | ', e.g. 1175 Ependymal NN_1 | 1176 Ependymal NN_2

## For these, we need to convert to accessions from wmb_data['annotations'] where each entry has keys 'cell_set_accession' and 'cell_label'
## First step - look up cell_set_accession for each label and substitute. Results should be accessions separated by '|' if multiple (no spaces)
## Second step - split into two row, one for multiples and one for single.

# Build label to accession mapping from wmb_data['annotations']
label_to_accession = {entry['cell_label']: entry['cell_set_accession'] for entry in wmb_data['annotations']}

def labels_to_accessions(label_str):
    labels = [lbl.strip() for lbl in label_str.split('|') if lbl.strip()]
    accessions = [label_to_accession.get(lbl, '') for lbl in labels]
    # Add WMB: prefix to each accession if not empty
    accessions = [f"WMB:{acc}" if acc and not acc.startswith("WMB:") else acc for acc in accessions]
    return '|'.join([acc for acc in accessions if acc])

new_rows = []
robot_template_header = {'Group': '',
                         'Type': 'TYPE',
        'accession_group': 'ID',
        'curated_ABC_WMB_supertype_single_accession': 'AI skos:exactMatch SPLIT=| ',
        'curated_ABC_WMB_supertype_multi_accession': 'AI skos:relatedMatch SPLIT=| '
}

new_rows.append(robot_template_header)

for idx, row in WMB_AT.iterrows():
    group = row.get('Group', '')
    accession_group = row.get('accession_group', '')
    supertype_labels = str(row.get('curated_ABC_WMB_supertype', ''))
    cluster_labels = str(row.get('curated_ABC_WMB_cluster', ''))
    supertype_accessions = labels_to_accessions(supertype_labels)
    cluster_accessions = labels_to_accessions(cluster_labels)
    # Single accession if only one, else multi
    supertype_split = supertype_accessions.split('|') if supertype_accessions else []
    if len(supertype_split) == 1:
        supertype_single = supertype_accessions
        supertype_multi = ''
    elif len(supertype_split) > 1:
        supertype_single = ''
        supertype_multi = supertype_accessions
    else:
        supertype_single = ''
        supertype_multi = ''

    new_rows.append({
        'Group': group,
        'Type': 'owl:NamedIndividual',
        'accession_group': f"BG:{accession_group}",
        'curated_ABC_WMB_supertype_single_accession': supertype_single,
        'curated_ABC_WMB_supertype_multi_accession': supertype_multi
    })

new_table = pd.DataFrame(new_rows)
print(new_table.head())

new_table.to_csv('src/templates/BG2WMB_AT_map_template.tsv', sep='\t', index=False)





