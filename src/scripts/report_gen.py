

import argparse
import json
import sys
import pandas as pd
import csv
from pathlib import Path
import importlib.util
import os
import io

# Robust import for neo4j_bolt_wrapper
def import_neo4j_bolt_wrapper():
    wrapper_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils', 'neo4j_bolt_wrapper.py'))
    spec = importlib.util.spec_from_file_location('neo4j_bolt_wrapper', wrapper_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['neo4j_bolt_wrapper'] = module
    spec.loader.exec_module(module)
    return module

neo4j_bolt_wrapper = import_neo4j_bolt_wrapper()
Neo4jBoltQueryWrapper = neo4j_bolt_wrapper.Neo4jBoltQueryWrapper

# Query library included directly
class Neo4jNamedQueries:
    REPORT_BG_MAPPINGS = '''
    MATCH (tax:Individual)-[:annotations]->(cell_set:Cell_cluster)-[:has_labelset]->(ls:Individual) 
    WHERE tax.title = ['HMBA Basal Ganglia Consensus Taxonomy']
    AND ls.label_rdfs = ['Group'] 
    AND NOT (cell_set)-[:subcluster_of*0..]->(:Cell_cluster { label_rdfs: ['Nonneuron']})
    MATCH (cell_set)-[:subcluster_of*0..]->(cc2:Cell_cluster)-[:has_labelset]->(ls2)
    OPTIONAL MATCH (cc2)-[:composed_primarily_of]->(c:Cell)
    OPTIONAL MATCH (cell_set)-[:exactMatch]->(at:Cell_cluster)-[:has_labelset]->(ls3)
    RETURN DISTINCT cell_set.label_rdfs[0] AS Group, 
    COLLECT(DISTINCT({ id: c.curie, name: c.label_rdfs[0], 
                       labelset: ls2.label_rdfs[0], 
                       cell_set: cc2.label_rdfs[0]})) AS cl_mappings,
    collect(distinct{ labelset: ls3.label_rdfs[0], 
                      cell_set: at.label_rdfs[0]}) AS WMB_AT,
        cell_set.rationale_dois AS refs, 
    SIZE([x IN COLLECT(c.curie) WHERE x IS NOT NULL]) = 0 AS no_cl_mapping 
    ORDER BY no_cl_mapping DESC 
    ;
    '''
    # Add more named queries as needed

def pretty_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Run named Neo4j queries and output TSV.")
    parser.add_argument('--args', type=str, required=True, help='JSON string or path to JSON file with args')
    parser.add_argument('--query', type=str, required=True, help='Named query to run')
    parser.add_argument('--endpoint', type=str, required=True, help='Neo4j bolt endpoint')
    parser.add_argument('--user', type=str, default=None, help='Neo4j username')
    parser.add_argument('--password', type=str, default=None, help='Neo4j password')
    parser.add_argument('--output', type=str, default=None, help='Output TSV file path')
    args = parser.parse_args()

    # Load JSON args
    if Path(args.args).exists():
        with open(args.args) as f:
            query_args = json.load(f)
    else:
        query_args = json.loads(args.args)

    # Get query string
    query_str = getattr(Neo4jNamedQueries, args.query, None)
    if not query_str:
        print(f"Query '{args.query}' not found in Neo4jNamedQueries.", file=sys.stderr)
        sys.exit(1)

    # Connect and run query
    wrapper = Neo4jBoltQueryWrapper(args.endpoint, args.user, args.password)
    results = wrapper.run_query(query_str, query_args, return_type=None)

    # Convert results to DataFrame
    if not results:
        print("No results returned.")
        sys.exit(0)
    df = pd.DataFrame(results)

    # Pretty print any object cells as JSON, quoted for TSV/CSV compatibility
    def pretty_json_cell(x):
        if isinstance(x, (dict, list)):
            return json.dumps(x, indent=2, ensure_ascii=False)
        return x

    for col in df.columns:
        df[col] = df[col].apply(pretty_json_cell)

    # Output TSV with quoting for multiline compatibility using csv writer (RFC4180 style)
    def write_tsv_with_csv(df, output_path=None):
        # Prepare rows
        rows = []
        cols = list(df.columns)
        for _, r in df.iterrows():
            row = []
            for c in cols:
                v = r[c]
                if pd.isna(v):
                    row.append("")
                else:
                    row.append(str(v))
            rows.append(row)

        if output_path:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_ALL, lineterminator='\n')
                writer.writerow(cols)
                writer.writerows(rows)
        else:
            buf = io.StringIO()
            writer = csv.writer(buf, delimiter='\t', quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writerow(cols)
            writer.writerows(rows)
            # print without adding extra newline
            sys.stdout.write(buf.getvalue())

    if args.output:
        write_tsv_with_csv(df, args.output)
    else:
        write_tsv_with_csv(df, None)

if __name__ == "__main__":
    main()