# Variables
BG2WMB_TEMPLATE = src/templates/BG2WMB_AT_map_template.tsv
BG2WMB_OWL = owl/BG2WMB.owl
REPORTS_DIR = reports
REPORT_BG_MAPPINGS = $(REPORTS_DIR)/BG_mappings.csv
NEO4J_BOLT ?= bolt://localhost:7687

.PHONY: all template owl report_BG_mappings report_BG_mappings_md fetch_bg2wmb_mappings
# Download MWB_consensus_homology.csv from Google Sheets
fetch_bg2wmb_mappings:
	python3 src/scripts/fetch_bg2wmb_mappings.py

all: template owl 

# Build the ROBOT template TSV file
template:
	python src/scripts/WMB_AT_map.py

# Convert the ROBOT template to OWL
owl: $(BG2WMB_TEMPLATE)
	robot template \
		--add-prefix "BG: https://purl.brain-bican.org/ontology/CS20250428/" \
		--add-prefix "WMB: https://purl.brain-bican.org/taxonomy/CCN20230722/" \
		-t $(BG2WMB_TEMPLATE) \
		-o $(BG2WMB_OWL)

# Run report_BG_mappings and dump output to reports folder

# Always generate CSV and Markdown from cypher query
report_BG_mappings: | $(REPORTS_DIR)
	python src/scripts/report_gen.py \
		--args '{}' \
		--query REPORT_BG_MAPPINGS \
		--endpoint $(NEO4J_BOLT) \
		--output $(REPORT_BG_MAPPINGS)

report_BG_mappings_md: report_BG_mappings
	@echo "Markdown report generated at reports/BG_mappings.md"

# Ensure reports directory exists
$(REPORTS_DIR):
	@mkdir -p $(REPORTS_DIR)
