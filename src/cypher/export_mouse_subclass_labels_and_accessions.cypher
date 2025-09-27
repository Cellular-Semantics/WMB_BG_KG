// Cypher query to export mouse subclass labels and accessions for mapping
// This query retrieves all mouse subclass labels and their IRIs (accessions)
// for use in mapping tables and reporting.
//
// Example output columns: label\taccession




MATCH (ds { title: ['Whole Mouse Brain Taxonomy']})
	  -[:annotations]->(cc:Cell_cluster)-[:has_labelset]
	  -(:Individual { label: 'subclass'}) 
	  RETURN cc.label AS label, cc.iri AS accession
	  ORDER BY accession ASC;