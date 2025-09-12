# WMB_KG

[OBASK pipeline](https://github.com/OBASKTools/obask) for WMB_KG + BG

Currently loads WMBO & BGO + WMBO:BG annotation transfer mappings built in this repo.

Mappings currently only cover WMB:supertype to BG:group.  Others pending.

Above may be out of date, so see `config/collectdata/vfb_fullontologies.txt` to check current ontologies loaded.

To run the pipeline:  `docker compose up`

To build the annotation transfer file: `make all`  (requires ROBOT)

## Some useful Cypher queries

Report on CL mappings + annotation transfers

```cypher
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

```
