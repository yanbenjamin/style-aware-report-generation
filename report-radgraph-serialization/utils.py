"""This ancillary module provides helper functions for the serialization modules 
(subgraphs_method, entity_method), e.g. building NetworkX graphs """

import networkx as nx

def build_graph(sample):
    """
    Creates a directed graph using the given sample data.

    Args:
        sample (dict): A dictionary containing "entities" and "text" keys.

    Returns:
        networkx.DiGraph: A directed graph representing the entities and relations in the sample.
    """
    G = nx.DiGraph()

    # Add nodes for each entity
    for entity_id, entity_data in sample["entities"].items():
        G.add_node(entity_id, label=entity_data["label"], tokens=entity_data["tokens"])

    # Add edges for each relation
    for entity_id, entity_data in sample["entities"].items():
        for relation in entity_data["relations"]:
            relation_type, related_entity_id = relation
            G.add_edge(entity_id, related_entity_id, relation_type=relation_type)

    return G

def get_subgraphs(G):
    """
    Gets all the weakly connected components in the given directed graph.

    Args:
        G (networkx.DiGraph): A directed graph.

    Returns:
        list of networkx.DiGraph: A list of subgraphs, where each subgraph represents
        a weakly connected component in the input graph.
    """
    weakly_connected_components = list(nx.weakly_connected_components(G))

    merged_graphs = []
    for component in weakly_connected_components:
        # Create a new graph with merged nodes and edges
        H = nx.DiGraph()
        for node in component:
            H.add_node(node)
        H.add_edges_from(G.subgraph(component).edges())

        # Add the new graph to the list of merged graphs
        merged_graphs.append(H)

    return merged_graphs

def section_start(tokens, header_name = "FINDINGS"):
    """
    finds the token index that is start of a given section
    
    Args:
        tokens (list[str]): A list of tokens that compose a radiology report 
        header_name (str): The header name of the section (typically capitalized)
       
    Returns:
        int: the index within tokens where the section begins
    """
        
    #a semi-colon (:) follows the section headings
    header_tokens = [header_token.strip() for header_token in header_name.split(" ")] + [":"]
    
    for token_ix, token in enumerate(tokens):
        if (token_ix >= len(tokens) - len(header_tokens)): #index out of bounds
            continue
        
        #check the len(header_tokens) starting at token_ix and see if there is a match
        report_tokens = tokens[token_ix: token_ix + len(header_tokens)]
        if (report_tokens == header_tokens):
            return token_ix

    return -1 #no section found

def isHeaderPrefix(prefix):
    """
    checks whether the word before a semi-colon (prefix) corresponds to a report section header,
    mostly to excise edge cases such as when a semi-colon is used to signify time in the report.
    
    Args:
        prefix (str): A string of a single token such as INDICATION, CONCLUSION, COMPARISON
        
    Returns:
        bool: whether the prefix corresponds to a section header or not 

    """
    for syntax_token in ["_", "!",",","."]: 
        if (syntax_token in prefix):
            return False 
    if (prefix.isnumeric() == True or prefix.isupper() == False):
        return False
    return True

def section_end(tokens, section_start_idx, header_name = "FINDINGS"):
    """
    finds the token index that is the end of a given section
    
    Args:
        tokens (list[str]): A list of tokens that compose a radiology report 
        section_start_idx (int): The index within tokens where the section starts
        header_name (str): The header name of the section (typically capitalized)
       
    Returns:
        int: the index within tokens where the section ends
    """
    
    #header name starts there, look for a semi-colon which is the end,
    header_tokens = [header_token.strip() for header_token in header_name.split(" ")] + [":"]
    section_content_start = section_start_idx + len(header_tokens)
    for token_ix, token in enumerate(tokens[section_content_start:]): #token is not shifted!
        prefix = tokens[section_content_start + token_ix - 1]
        if (token == ":" and isHeaderPrefix(prefix) == True):
            #backtrack 
            ending_idx = token_ix + section_content_start
            while (ending_idx >= 1 and isHeaderPrefix(tokens[ending_idx - 1]) == True):
                ending_idx -= 1
            
            if (ending_idx - 1 != section_start_idx + len(header_name.split(" "))):
                return ending_idx
                   
    return len(tokens)

def locate_findings_impression(report_text):
    """
    retrieves the index ranges for the FINDINGS and IMPRESSION sections of the RadGraph text,
    where the indices pertain to the word-level tokens

    Args:
        report_text (str): A string of the RadGraph's corresponding free-text report in MIMIC-CXR
        
    Returns:
        tuple[int], tuple[int]: the first tuple is comprised of (start idx of FINDINGS, end idx of FINDINGS),
                                    and (-1,-1) if a FINDINGS section was not found
                                the second tuple is comprised of (start idx of IMPRESSION, end idx of IMPRESSION),
                                    and (-1,-1) if an IMPRESSION section was not found.
    """
    tokens = report_text.split(" ")

    #determining if findings and impression sections are lumped together in report
    findings_and_impression_idx = section_start(tokens, header_name = "FINDINGS AND IMPRESSION")
    if (findings_and_impression_idx != -1): 
        section_end_idx = section_end(tokens, findings_and_impression_idx, header_name = "FINDINGS AND IMPRESSION")
        return (findings_and_impression_idx, section_end_idx), (findings_and_impression_idx, section_end_idx)
    
    #getting the start index for the findings section
    findings_start_idx = section_start(tokens, header_name = "FINDINGS")

    #multiple possible headers for impression
    impression_headers = ['IMPRESSION', 'CONCLUSION', 'SUMMARY']
    for impression_header in impression_headers:
        impression_start_idx = section_start(tokens, header_name = impression_header)
        if (impression_start_idx != -1):
            break 
    
    #get the terminus of the FINDINGS and IMPRESSION sections
    findings_end_idx = section_end(tokens, findings_start_idx, header_name = "FINDINGS") if findings_start_idx != -1 else -1
    impression_end_idx = section_end(tokens, impression_start_idx, header_name = "IMPRESSION") if impression_start_idx != -1 else -1
    return (findings_start_idx, findings_end_idx), (impression_start_idx, impression_end_idx)

def categorize_node(obj, node, findings_idx_range, impression_idx_range):
    """
    determines whether a node entity belongs to the FINDINGS or IMPRESSION section in the report.
    Note: Calling this function assumes that at least one of the FINDINGS and IMPRESSION sections exist,
          and that they do not coincide if both exist. See graph_report.serialize_graph_by_entities() for
          how this is handled. 

    Args:
        obj (dict): a RadGraph json object
        node (int): an entity_id of the RadGraph
        findings_idx_range (tuple[int]): A tuple of the form (findings_start_idx, findings_end_idx), detailing 
                                         the indexed range of tokens in the FINDINGS section
        impression_idx_range (tuple[int]): A tuple of the form (impression_start_idx, impression_end_idx), detailing
                                         the indexed range of tokens in the IMPRESSION section

    Returns:
        str: the section that the node entity belongs to
        
    """
    start_idx, end_idx = obj["entities"][node]["start_ix"], obj["entities"][node]["end_ix"]
    (findings_start, findings_end), (impression_start, impression_end) = findings_idx_range, impression_idx_range
    
    if (findings_start == -1 and impression_start == -1):
        raise ValueError("At least one of the FINDINGS and IMPRESSION sections must exist")
    elif (findings_start == impression_start):
        raise ValueError("The FINDINGS and IMPRESSION sections should not coincide.")   
    elif (findings_start == -1 and impression_start != -1): #no findings section explicitly delineated
        if (start_idx >= impression_start and end_idx < impression_end):
            return "IMPRESSION"
        return "FINDINGS"
    #a findings section is explicitly delineated
    if (start_idx >= findings_start and end_idx < findings_end):
        return "FINDINGS"
    return "IMPRESSION"
        
def categorize_subgraph(obj, subgraph, findings_idx_range, impression_idx_range):
    """
    determines whether a subgraph belongs to the FINDINGS or IMPRESSION section in the report
    Note: Calling this function assumes that at least one of the FINDINGS and IMPRESSION sections exist,
          and that they do not coincide if both exist. See graph_report.serialize_graph_by_entities() for
          how this is handled. 

    Args:
        obj (dict): a RadGraph json object
        subgraph (networkx.DiGraph): A directed graph representing a weakly connected component
        findings_idx_range (tuple[int]): A tuple of the form (findings_start_idx, findings_end_idx), detailing 
                                         the indexed range of tokens in the FINDINGS section
        impression_idx_range (tuple[int]): A tuple of the form (impression_start_idx, impression_end_idx), detailing
                                         the indexed range of tokens in the IMPRESSION section

    Returns:
        str: the section that the subgraph belongs to
        
    """
    nodes = subgraph.nodes
    sections = set() #filters automically to remove distinct elements
    for node in nodes: 
        sections.add(categorize_node(obj, node, findings_idx_range, impression_idx_range))
       
    if (sections == {"FINDINGS"}): #all node entities were within the FINDINGS section  
        return "FINDINGS"
    if (sections == {"IMPRESSION"}): #all node entities were within the IMPRESSION section 
        return "IMPRESSION"
    
    return "IMPRESSION" # as a tie-breaker in case node entities are heterogeneous
    
def get_suffix(node_label, stem = "@ "): 
  """
  obtains the suffix for the node serialization based on its RadGraph entity label 

  Args:
    node_label (str): The node's label as defined by the RadGraph dataset
    stem (str): Preposition to be used for prompting, e.g. {"@ ", "is ", "", "at "}
  
  Returns: 
    str: the suffix to be appended to the node serialization, which depends 
    on whether the node entitity is present, uncertain, or absent. 

  """
  if ("DP" in node_label):
    return "{}present".format(stem)
  elif ("U" in node_label):
    return "{}uncertain".format(stem)
  elif ("DA" in node_label):
    return "{}absent".format(stem)
  return ""
