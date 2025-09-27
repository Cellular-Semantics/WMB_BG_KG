"""
Script to export mouse subclass labels and accessions using the Neo4j bolt wrapper in utils.
Outputs a TSV file for downstream mapping/reporting use.
"""

import importlib.util

import argparse
from pathlib import Path

# Find project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent  # Go up from scripts -> src -> project_root

# Direct import of neo4j wrapper without sys.path manipulation
wrapper_path = project_root / 'src' / 'utils' / 'neo4j_bolt_wrapper.py'
spec = importlib.util.spec_from_file_location('neo4j_bolt_wrapper', wrapper_path)
neo4j_wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_wrapper)
Neo4jBoltQueryWrapper = neo4j_wrapper.Neo4jBoltQueryWrapper

# Define paths directly
CYPHER_DIR = project_root / 'src' / 'cypher'

CY_FILE = CYPHER_DIR / 'export_mouse_subclass_labels_and_accessions.cypher'


def main():
    parser = argparse.ArgumentParser(description="Export mouse subclass labels and accessions from Neo4j.")
    parser.add_argument('-o', '--output', type=str, default=None, help='Output TSV file path')
    args = parser.parse_args()

    out_file = Path(args.output) if args.output else (project_root / 'resources/mouse_cc_label_iri.tsv')

    with open(CY_FILE, 'r') as f:
        cypher = f.read()

    # Use Neo4jBoltQueryWrapper to run query
    wrapper = Neo4jBoltQueryWrapper("bolt://localhost:7687", test_connection=True)
    results = wrapper.run_query(cypher, return_type=None)

    # Expecting results as list of dicts with 'label' and 'accession'
    with open(out_file, 'w') as out:
        out.write('label\taccession\n')
        for row in results:
            out.write(f"{row['label']}\t{row['accession']}\n")
    print(f"Exported {len(results)} rows to {out_file}")

if __name__ == '__main__':
    main()
