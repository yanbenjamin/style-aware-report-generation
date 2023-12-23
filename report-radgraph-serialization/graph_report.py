"""This module extracts and serializes graph data from a JSON file
into a string report, with several serialization methods available for use.

Note: serialize_graph_report() -- the bottom function -- is the main wrapper that encompasses all methods
"""

from utils import *
import networkx as nx

ERROR_LABELS, ERROR_METHOD = -1, -2 #constants used for error handling

def serialize_subgraph(subgraph, G):
    """
    Serializes a subgraph into a string representation.

    Args:
        subgraph (networkx.DiGraph): A directed graph representing a weakly connected component.
        G (networkx.DiGraph): The original directed graph.

    Returns:
        str: A string representation of the subgraph, where nodes are sorted by their integer value
        and their "tokens" attributes are concatenated into a string.
        If a node has a "label" containing "DA", "no" is prepended to the string.
        If a node has a "label" containing "U", "maybe" is prepended to the string.
    """
    sorted_nodes = sorted(subgraph.nodes, key=lambda x: int(x))
    out = ""
    previous_node_modified = False
    for node in sorted_nodes:
        node_label = G.nodes[node]["label"]
        node_tokens = G.nodes[node]["tokens"]
        if "DA" in node_label and not previous_node_modified:
            out = "no " + out #prepend the no to the subgraph serialization
            previous_node_modified = True
        elif "U" in node_label and not previous_node_modified:
            out = "maybe " + out #prepend the maybe to the subgraph serialization
            previous_node_modified = True
        out += node_tokens + " "

    return out

def serialize_graph_by_subgraphs(obj, separate_findings_impression = False):
    """
    Serializes a JSON object into a string report of its entities and relations, using a subgraph decomposition method.

    Specifically, the function takes in a JSON object containing entities and their relations as input
    and creates a directed graph representation of the data using the networkx library.
    It then extracts weakly connected subgraphs from the graph and serializes each subgraph
    into a string representation. The module outputs a report string containing the serialized subgraphs,
    one per line.

    Args:
        obj (dict): A RadGraph JSON object
        separate_findings_impression (bool): If True, separates the findings and impressions in the 
                    serialization into separate, labeled sections. 

    Returns:
        str: A string representation of the graph report, where each non-header line represents
        a subgraph in the input JSON object. The headers are FINDINGS, IMPRESSION, and GENERAL, with the latter
        for any subgraphs whose entities aren't completely enclosed in either FINDINGS or IMPRESSION.
    """
    
    G = build_graph(obj)
    #ascertain where the findings and impression sections are inside the RadGraph report
    (findings_start_idx, findings_end_idx), (impression_start_idx, impression_end_idx) = locate_findings_impression(obj["text"])
    subgraphs = get_subgraphs(G)
    
    report_dict = {"report": "", "FINDINGS": "", "IMPRESSION": "", "FINDINGS AND IMPRESSION":""}
    
    for subgraph in subgraphs:
        serialized = serialize_subgraph(subgraph, G)
        report_dict["report"] += serialized.strip() + "\n"
        
        #determine section in the RadGraph report that the subgraph belongs in
        if (findings_start_idx == impression_start_idx or (findings_start_idx == -1 and impression_start_idx == -1)):
        #the findings and impression need to be unified
            subgraph_section = "FINDINGS AND IMPRESSION"
        else:
            subgraph_section = categorize_subgraph(obj, subgraph, (findings_start_idx, findings_end_idx), (impression_start_idx, impression_end_idx)) 
        
        report_dict[subgraph_section] += serialized + "\n" 

    if (separate_findings_impression == False):
        report = report_dict["report"]
    elif (report_dict["FINDINGS AND IMPRESSION"] != ""):
        report = "FINDINGS AND IMPRESSION \n" + report_dict["FINDINGS AND IMPRESSION"]
    elif (report_dict["FINDINGS"] != "" and report_dict["IMPRESSION"] == ""):
        #no subgraphs fall within the IMPRESSION section (all FINDINGS)
        report = "FINDINGS \n" + report_dict["FINDINGS"]
    elif (report_dict["FINDINGS"] == "" and report_dict["IMPRESSION"] != ""):
        #no subgraphs fall within the FINDINGS section (all IMPRESSION)
        report = "IMPRESSION \n" + report_dict["IMPRESSION"]
    else:
        report = "FINDINGS \n" + report_dict["FINDINGS"] + "\n" + "IMPRESSION \n" + report_dict["IMPRESSION"]
        
    return report

def serialize_node(graph_obj, source_node, stem = "@"):
  """
  returns a string representation of an entity node within the RadGraph

  Args:
    graph_obj (dict): The "entities" value of a RadGraph JSON object
    source_node (int): entity_id of the chosen RadGraph node 
    stem (str): see get_suffix method in utils.py for detail
  
  Returns: 
    str: a string representation of the source node and the target entities it 
    has a directed edge to. located_at relations are listed first, followed
    by modify and finally suggestive_of. 
  """

  #a lower precedence value means that relation is listed first in serialization
  relation_precedence = {"located_at": 1, "modify": 2, "suggestive_of": 3}

  #extract the entity information from the graph for this node 
  source_tokens = graph_obj[source_node]["tokens"]
  relations = graph_obj[source_node]["relations"]
  label = graph_obj[source_node]["label"]
  all_relation_types = set([rel[0] for rel in relations]) #set of distinct relation types

  #sort the relations by (1) precedence of relation as outlined in the dictionary above
  #and (2) index in the relation list
  relation_queue = {tuple(relation): (relation_precedence[relation[0]], 
                               index) for index, relation in enumerate(relations)}
  sorted_relations = sorted(relations, key = lambda rel: relation_queue[tuple(rel)])
  
  node_serialization = ""
  #special case: no relations, just the source token to be serialized
  if (len(relations) == 0):
    node_serialization += source_tokens + " "

  #special case: there is only modify relations for this node, and > 1 relation
  elif (all_relation_types == {"modify"} and len(relations) > 1): 
    for (relation_type, target_node) in sorted_relations:
      node_serialization += graph_obj[target_node]["tokens"] + " "
    node_serialization += source_tokens + " "
  
  #special case: there is only located_at relations for this node, and > 1 relation
  elif (all_relation_types == {"located_at"} and len(relations) > 1):
    node_serialization += source_tokens + " "
    if ("DP" in label): #only add relation types if entity is actually present 
      for (relation_type, target_node) in sorted_relations:
        node_serialization += relation_type + " " + graph_obj[target_node]["tokens"] + " "
  
  else: #general case 
    for index, (relation_type, target_node) in enumerate(sorted_relations):
      if (relation_type == "modify"): #don't include the word "modify" in serialization 
        node_serialization += source_tokens + " " + graph_obj[target_node]["tokens"] + " "
      else: #write located_at and suggestive_of explicitly in serialization
        node_serialization += source_tokens + " " + relation_type + " " + graph_obj[target_node]["tokens"] + " "
      node_serialization += ", " if (index != len(sorted_relations) - 1) else " "
      
  return node_serialization + get_suffix(label, stem)

def serialize_graph_by_entities(obj, method_name = "no_sep", separate_findings_impression = False):
  """
  returns a string serialiation of a RadGraph JSON object, using entity-level representations
  Specifically, the function iterates over all nodes, creates a serialization 
  of that node and the entities it has a directed edge into, and concatenates
  these serializations into a single report string, one per line.

  Args:
    obj (dict): A RadGraph JSON object
    method_name (str): The method used for serializing reports. Should be among
                {"no_sep", "with_anat", "with_@_anat"}. The latter two separate the anatomical
                and observation entities, with the third using a slightly different suffix (@)
                than the second. The first does not separate them. 
    separate_findings_impression (bool): If True, separates the findings and impressions in the 
                    serialization into separate, labeled sections.
  
  Returns: 
    str: a string representation of the source node and the target entities it 
    has a directed edge to. located_at relations are listed first, followed
    by modify and finally suggestive_of. 
  """

  graph_obj = obj["entities"]
  (findings_start_idx, findings_end_idx), (impression_start_idx, impression_end_idx) = locate_findings_impression(obj["text"])
  nodes = list(graph_obj.keys())
     
  #segment the intermediate serializations into RadGraph report sections, with "report"
  #bundling all sections together without separation. 
  report_dict = {"report": "", "FINDINGS": "", "IMPRESSION": "", "FINDINGS AND IMPRESSION":""}

  #iterate through the graph nodes and serialize each
  for node in nodes: 
    label = graph_obj[node]["label"]
    node_serialization = ""
    if (method_name == "with_@_anat" and label != "ANAT-DP"): #exclude anatomical entities
      node_serialization = serialize_node(graph_obj, node, stem = "@ ") + "\n"
    
    elif (method_name == "with_anat" and label != "ANAT-DP"): #exclude anatomical entities
      stem = "is " if len(graph_obj[node]["relations"]) > 0 else ""
      node_serialization = serialize_node(graph_obj, node, stem = stem) + "\n"
        
    elif (method_name == "no_sep"): #don't exclude anatomical entities if method is NO_SEP
      node_serialization = serialize_node(graph_obj, node, stem = "@ ") + "\n"
    
    report_dict["report"] += node_serialization
    
    #determine section in the RadGraph report that the subgraph belongs in
    if (findings_start_idx == impression_start_idx or (findings_start_idx == -1 and impression_start_idx == -1)):
        #the findings and impression need to be unified
        node_section = "FINDINGS AND IMPRESSION"
    else: 
        node_section = categorize_node(obj, node, (findings_start_idx, findings_end_idx),
                                               (impression_start_idx, impression_end_idx)) 
    report_dict[node_section] += node_serialization 
    
  if (separate_findings_impression == False): #no stratification of the serialization into RadGraph sections 
    report = report_dict["report"]
  elif (report_dict["FINDINGS AND IMPRESSION"] != ""):
    report = "FINDINGS AND IMPRESSION \n" + report_dict["FINDINGS AND IMPRESSION"]
  elif (report_dict["FINDINGS"] != "" and report_dict["IMPRESSION"] == ""):
    #no subgraphs fall within the IMPRESSION section (all FINDINGS)
    report = "FINDINGS \n" + report_dict["FINDINGS"]
  elif (report_dict["FINDINGS"] == "" and report_dict["IMPRESSION"] != ""):
    #no subgraphs fall within the FINDINGS section (all IMPRESSION)
    report = "IMPRESSION \n" + report_dict["IMPRESSION"]
  else:
    report = "FINDINGS \n" + report_dict["FINDINGS"] + "\n" + "IMPRESSION \n" + report_dict["IMPRESSION"]

  #gather a list of the anatomical nodes if relevant to method
  if (method_name in ["with_@_anat", "with_anat"]):
    anat_structures = [graph_obj[node]["tokens"] for node in nodes if graph_obj[node]["label"] == "ANAT-DP"]
    anat_structures_str = ",".join(anat_structures)
    report += "Anatomical structures present: {}\n".format(anat_structures_str)
  
  return report

def serialize_graph_report(obj, method, separate_findings = False, labeler = None): 
    """
    a wrapper function to serialize graphs according to the method specified
    
    Args: 
        obj (dict): a RadGraph json object
        method (str): name of serialization method, out of {"subgraphs", "no_sep", "with_anat", "with_@_anat"}
        separate_findings (bool): If True, separates the findings and impressions in the 
                    serialization into separate, labeled sections.
    
    Returns: 
        str: upon success, the serialized text representation of the graph obj. upon error, 
             it returns a negative int
    """
    
    if ("entities" not in obj): #the case of multiple radiologist labelers
        labeler_keys = sorted([key for key in obj.keys() if "labeler" in key])
        #error: no labels provided for the RadGraph object
        if len(labeler_keys) == 0: return ERROR_LABELS
    
        #otherwise, select one labeler to fill in the object's canonical entities
        obj_labeled = obj.copy() 
        obj_labeled["entities"] = obj[labeler_keys[0]]["entities"]

        #recursive call on the modified object to get the serialization
        return serialize_graph_report(obj_labeled, method, separate_findings)

    if (method == "subgraphs"):
        #decomposes graph into weakly connected subgraphs, and serializes each subgraph prior to concatenation.
        return serialize_graph_by_subgraphs(obj, separate_findings_impression = separate_findings)

    elif (method in {"no_sep", "with_anat", "with_@_anat"}):
        #serializes each node-level entity (instead of subgraph-level) of the graph, and then concatenates the string representations
        return serialize_graph_by_entities(obj, method_name = method, separate_findings_impression = separate_findings)

    #error: invalid method specified (must be either subgraphs, no_sep, with_anat, with_@_anat)
    return ERROR_METHOD