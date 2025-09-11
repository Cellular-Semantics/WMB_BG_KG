BG2WMB_TEMPLATE = src/templates/BG2WMB_AT_map_template.tsv
BG2WMB_OWL = owl/BG2WMB.owl

.PHONY: all template owl

all: template owl

# Build the ROBOT template TSV file
# (Python script must be run from repo root)
template:
	python src/scripts/WMB_AT_map.py

# Convert the ROBOT template to OWL
owl: $(BG2WMB_TEMPLATE)
	robot template \
		--add-prefix "BG: https://purl.brain-bican.org/ontology/CS20250428/" \
		--add-prefix "WMB: https://purl.brain-bican.org/taxonomy/CCN20230722/" \
		-t $(BG2WMB_TEMPLATE) \
		-o $(BG2WMB_OWL)
