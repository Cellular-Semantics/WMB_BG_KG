

import argparse
import json
import sys
import pandas as pd
import csv
from pathlib import Path
import importlib.util
import os
import io

# Find project root and import neo4j wrapper
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent

# Direct import of neo4j wrapper
wrapper_path = project_root / 'src' / 'utils' / 'neo4j_bolt_wrapper.py'
spec = importlib.util.spec_from_file_location('neo4j_bolt_wrapper', wrapper_path)
neo4j_wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_wrapper)
Neo4jBoltQueryWrapper = neo4j_wrapper.Neo4jBoltQueryWrapper

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

def main():
    parser = argparse.ArgumentParser(description="Run named Neo4j queries and output TSV.")
    parser.add_argument('--args', type=str, required=True, help='JSON string or path to JSON file with args')
    parser.add_argument('--query', type=str, required=True, help='Named query to run')
    parser.add_argument('--endpoint', type=str, required=False, default=None, help='Neo4j bolt endpoint')
    parser.add_argument('--dry-run', action='store_true', help='Run a local dry-run using mock results instead of Neo4j')
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

    # Connect and run query (or dry-run using mock data)
    if args.dry_run:
        # Create a small mock result to exercise CSV/MD generation
        results = [
            {
                'Group': 'TEST Group',
                'cl_mappings': [
                    {'id': 'CL:0000001', 'name': 'test cell', 'labelset': 'Group', 'cell_set': 'TEST Group'}
                ],
                'WMB_AT': [
                    {'labelset': 'supertype', 'cell_set': '0123 TEST Supertype'}
                ],
                'refs': ['https://doi.org/example'],
                'no_cl_mapping': False
            }
        ]
    else:
        wrapper = Neo4jBoltQueryWrapper(args.endpoint, args.user, args.password)
        results = wrapper.run_query(query_str, query_args, return_type=None)

    # Convert results to DataFrame
    if not results:
        print("No results returned.")
        sys.exit(0)
    df = pd.DataFrame(results)

    # Pretty print any object cells as JSON, quoted for TSV/CSV compatibility
    def dicts_to_excel_multiline(dicts):
        try:
            return "\r\n".join(f"{d.get('labelset','')}: {d.get('cell_set','')}" for d in dicts)
        except Exception:
            return str(dicts)

    def dict_to_multiline(kv):
        try:
            return "\r\n".join(f"{k}: {v}" for k, v in kv.items())
        except Exception:
            return str(kv)

    def excel_cell_formatter(x):
        # Lists of dicts -> concise multiline key:value pairs
        if isinstance(x, list) and x and all(isinstance(i, dict) for i in x):
            return dicts_to_excel_multiline(x)
        # Single dict -> key: value lines
        if isinstance(x, dict):
            return dict_to_multiline(x)
        # Other lists -> one item per line
        if isinstance(x, list):
            return "\r\n".join(str(i) for i in x)
        return x

    # Output TSV with quoting for multiline compatibility using csv writer (RFC4180 style)
    def write_csv_with_csv(df, output_path=None):
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
                writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL, lineterminator='\r\n')
                writer.writerow(cols)
                writer.writerows(rows)
        else:
            buf = io.StringIO()
            writer = csv.writer(buf, delimiter=',', quoting=csv.QUOTE_ALL, lineterminator='\r\n')
            writer.writerow(cols)
            writer.writerows(rows)
            # print without adding extra newline
            sys.stdout.write(buf.getvalue())

    # Prepare CSV: compact single-line JSON for object cells
    def compact_json_cell(x):
        if isinstance(x, (dict, list)):
            return json.dumps(x, separators=(',', ':'), ensure_ascii=False)
        return x

    df_csv = df.copy()
    for col in df_csv.columns:
        df_csv[col] = df_csv[col].apply(compact_json_cell)

    # Write CSV (comma-delimited) using CRLF and UTF-8
    csv_output = args.output or 'reports/report.csv'
    write_csv_with_csv(df_csv, csv_output)

    # Prepare Markdown: pretty-printed JSON with <br> for newlines
    def pretty_html_cell(x):
        if isinstance(x, (dict, list)):
            pretty = json.dumps(x, indent=2, ensure_ascii=False)
            # replace newlines with <br> and preserve indentation with &nbsp;
            return '<br>'.join(line.replace(' ', '&nbsp;') for line in pretty.splitlines())
        return str(x)

    md_lines = []
    cols = list(df.columns)
    # Header
    md_lines.append('| ' + ' | '.join(cols) + ' |')
    md_lines.append('| ' + ' | '.join(['---'] * len(cols)) + ' |')
    for _, r in df.iterrows():
        cells = [pretty_html_cell(r[c]) for c in cols]
        md_lines.append('| ' + ' | '.join(cells) + ' |')

    md_output = Path(csv_output).with_suffix('.md')

    # Append the exact query and the passed parameters to the Markdown report
    query_section_lines = []
    query_section_lines.append('')
    query_section_lines.append('## Query')
    query_section_lines.append('')
    query_section_lines.append('```cypher')
    # Preserve the query formatting
    for line in (query_str or '').splitlines():
        query_section_lines.append(line)
    query_section_lines.append('```')

    # Add parameters used for the query, if any
    try:
        has_params = bool(query_args)
    except NameError:
        has_params = False

    if has_params:
        query_section_lines.append('')
        query_section_lines.append('## Parameters')
        query_section_lines.append('')
        query_section_lines.append('```json')
        # Pretty-print parameters for human readability
        query_section_lines.append(json.dumps(query_args, indent=2, ensure_ascii=False))
        query_section_lines.append('```')

    md_content = '\n'.join(md_lines) + '\n' + '\n'.join(query_section_lines) + '\n'
    md_output.write_text(md_content, encoding='utf-8')

if __name__ == "__main__":
    main()