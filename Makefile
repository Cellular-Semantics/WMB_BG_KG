# Template generation
TEMPLATES_DIR = src/templates
SILETTI_AT_MAP = resources/scFAIR_Siletti_WMB_mapping/scFAIR_Siletti_AT_map.tsv
WMB_WHB_TEMPLATE = $(TEMPLATES_DIR)/scFAIR_WHB_WMB_template.tsv
BG2WMB_TEMPLATE = $(TEMPLATES_DIR)/BG2WMB_AT_map_template.tsv

# OWL files
OWL_DIR = owl
BG2WMB_OWL = $(OWL_DIR)/BG2WMB.owl
SCFAIR_WHB_WMB_OWL = $(OWL_DIR)/scFAIR_WHB_WMB.owl

# Variables for maps
MAPS_DIR = resources/maps
CELL_SET_MAP = $(MAPS_DIR)/cell_set_map.tsv

# Report variables
REPORTS_DIR = reports
REPORT_BG_MAPPINGS = $(REPORTS_DIR)/BG_mappings.csv
NEO4J_BOLT ?= bolt://localhost:7687

.PHONY: all templates owl maps report_BG_mappings report_BG_mappings_md fetch_bg2wmb_mappings export_mouse_subclass_labels_and_accessions

# Main goals
all: templates owl

# Generate all templates
templates: $(WMB_WHB_TEMPLATE) $(BG2WMB_TEMPLATE)

# Generate all OWL files
owl: $(BG2WMB_OWL) $(SCFAIR_WHB_WMB_OWL)

# Rule to generate the scFAIR WHB WMB template (input file must exist)
$(WMB_WHB_TEMPLATE): $(SILETTI_AT_MAP) src/scripts/generate_scFAIR_WHB_WMB_template.py
	python3 src/scripts/generate_scFAIR_WHB_WMB_template.py

# Rule to generate the BG2WMB template
$(BG2WMB_TEMPLATE): resources/MWB_consensus_homology.csv src/scripts/WMB_AT_map.py
	python src/scripts/WMB_AT_map.py

# Convert BG2WMB template to OWL
$(BG2WMB_OWL): $(BG2WMB_TEMPLATE)
	@mkdir -p $(OWL_DIR)
	robot template \
		--add-prefix "BG: https://purl.brain-bican.org/ontology/CS20250428/" \
		--add-prefix "WMB: https://purl.brain-bican.org/taxonomy/CCN20230722/" \
		-t $(BG2WMB_TEMPLATE) \
		-o $(BG2WMB_OWL)

# Convert scFAIR WHB WMB template to OWL
$(SCFAIR_WHB_WMB_OWL): $(WMB_WHB_TEMPLATE)
	@mkdir -p $(OWL_DIR)
	robot template \
		--add-prefix "WHB: https://purl.brain-bican.org/ontology/AIT_CS202210140/" \
		--add-prefix "WMB: https://purl.brain-bican.org/taxonomy/CCN20230722/" \
		--add-prefix "n2o: http://n2o.neo/property/custom#" \
		-t $(WMB_WHB_TEMPLATE) \
		-o $(SCFAIR_WHB_WMB_OWL)

# Generate all mapping files
maps: | $(MAPS_DIR)
	$(MAKE) export_mouse_subclass_labels_and_accessions
	python3 src/utils/generate_celll_set_map.py -o $(CELL_SET_MAP)

# Ensure maps directory exists
$(MAPS_DIR):
	@mkdir -p $(MAPS_DIR)

# Export mouse subclass labels and accessions for mapping (for notebook/report use)
export_mouse_subclass_labels_and_accessions:
	python3 src/scripts/export_mouse_subclass_labels_and_accessions.py -o resources/mouse_cc_label_iri.tsv

# Download MWB_consensus_homology.csv from Google Sheets
fetch_bg2wmb_mappings:
	python3 src/scripts/fetch_bg2wmb_mappings.py

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
