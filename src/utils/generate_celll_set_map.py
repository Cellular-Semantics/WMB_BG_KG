
"""
Utility to generate a cell set map TSV by querying the database using the Cypher query in src/cypher/cell_set_map.cypher.
Usage:
	python generate_celll_set_map.py -o <output_file.tsv>
"""

import argparse
from pathlib import Path
import importlib.util

# Find project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent

# Import Neo4jBoltQueryWrapper from utils.neo4j_bolt_wrapper
wrapper_path = project_root / 'src' / 'utils' / 'neo4j_bolt_wrapper.py'
spec = importlib.util.spec_from_file_location('neo4j_bolt_wrapper', wrapper_path)
neo4j_wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_wrapper)
Neo4jBoltQueryWrapper = neo4j_wrapper.Neo4jBoltQueryWrapper

# Cypher query file
CY_FILE = project_root / 'src' / 'cypher' / 'cell_set_map.cypher'

def main():
	parser = argparse.ArgumentParser(description="Generate cell set map TSV from Neo4j query.")
	parser.add_argument('-o', '--output', type=str, required=True, help='Output TSV file path')
	args = parser.parse_args()
	out_file = Path(args.output)

	with open(CY_FILE, 'r') as f:
		cypher = f.read()

	wrapper = Neo4jBoltQueryWrapper("bolt://localhost:7687", test_connection=True)
	results = wrapper.run_query(cypher, return_type=None)

	if not results:
		print("No results returned from query.")
		return

	# Write header and rows
	with open(out_file, 'w') as out:
		header = results[0].keys()
		out.write('\t'.join(header) + '\n')
		for row in results:
			out.write('\t'.join(str(row[h]) for h in header) + '\n')
	print(f"Exported {len(results)} rows to {out_file}")

if __name__ == '__main__':
	main()
