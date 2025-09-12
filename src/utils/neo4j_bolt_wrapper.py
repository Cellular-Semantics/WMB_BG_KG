import json
import csv
from neo4j import GraphDatabase, basic_auth

class Neo4jBoltQueryWrapper:
    def __init__(self, endpoint, user=None, password=None, test_connection=True):
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        if test_connection:
            self.connect()

    def connect(self):
        try:
            if self.user and self.password:
                self.driver = GraphDatabase.driver(self.endpoint, auth=basic_auth(self.user, self.password))
            else:
                self.driver = GraphDatabase.driver(self.endpoint)
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")

    def test_connection(self):
        if not self.driver:
            self.connect()
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single()[0] == 1
        except Exception as e:
            return False

    def run_query(self, query, parameters=None, return_type="json"):
        if not self.driver:
            self.connect()
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            records = [record.data() for record in result]
            if return_type == "json":
                return json.dumps(records, indent=2)
            elif return_type == "csv":
                if records:
                    keys = records[0].keys()
                    output = csv.StringIO()
                    writer = csv.DictWriter(output, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(records)
                    return output.getvalue()
                else:
                    return ""
            else:
                return records

class Neo4jNamedQueries:
    # Add named queries here
    REPORT_CL_MAPPINGS = '''
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
