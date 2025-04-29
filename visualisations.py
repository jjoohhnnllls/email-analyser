"""
Visualisations Module

This module creates visualizations of email data including
social network graphs of senders and recipients.
"""

import networkx as nx
import matplotlib.pyplot as plt
import logging
from email_parser import extract_sender, extract_recipients
import os

logger = logging.getLogger(__name__)

def create_social_graph(email_contents):
    """
    Create a social graph of email senders and recipients.
    
    Args:
        email_contents (list): List of raw email content strings
        
    Returns:
        networkx.Graph: Graph object representing the email network
    """
    logger.info("Creating social graph from email data")
    
    # Create empty directed graph
    graph = nx.DiGraph()
    
    # Process each email
    for i, email_content in enumerate(email_contents):
        if not email_content:
            continue
            
        logger.debug(f"Processing email {i+1} for social graph")
        
        # Extract sender and recipients
        sender_tuple = extract_sender(email_content)
        recipient_tuples = extract_recipients(email_content)
        
        if not sender_tuple[1] or not recipient_tuples:
            logger.debug(f"Skipping email {i+1} - missing sender or recipients")
            continue
        
        # Format sender node label: "Name <email>" or just "email" if no name
        sender_label = f"{sender_tuple[0]} <{sender_tuple[1]}>" if sender_tuple[0] else sender_tuple[1]
        
        # Add sender node if not in graph
        if not graph.has_node(sender_label):
            graph.add_node(sender_label, type='sender', email=sender_tuple[1], name=sender_tuple[0])
        
        # For each recipient
        for recipient_tuple in recipient_tuples:
            if not recipient_tuple[1]:  # Skip if no email
                continue
                
            # Format recipient node label: "Name <email>" or just "email" if no name
            recipient_label = f"{recipient_tuple[0]} <{recipient_tuple[1]}>" if recipient_tuple[0] else recipient_tuple[1]
            
            # Add recipient node if not in graph
            if not graph.has_node(recipient_label):
                graph.add_node(recipient_label, type='recipient', email=recipient_tuple[1], name=recipient_tuple[0])
            
            # Add edge from sender to recipient
            if not graph.has_edge(sender_label, recipient_label):
                graph.add_edge(sender_label, recipient_label)
                
    logger.info(f"Created social graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    return graph

def visualize_social_graph(graph, output_file=None):
    """
    Visualize the social graph and optionally save to a file.
    
    Args:
        graph (networkx.Graph): The social graph to visualize
        output_file (str, optional): Path to save the visualization
    """
    logger.info("Visualizing social graph")
    
    plt.figure(figsize=(15, 12))
    
    # Use spring layout for positioning nodes
    pos = nx.spring_layout(graph, k=0.15, iterations=50)
    
    # Get node colors based on whether they're primarily senders or recipients
    node_colors = []
    for node in graph.nodes():
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)
        
        if out_degree > in_degree:
            node_colors.append('lightblue')  # Primarily a sender
        elif in_degree > out_degree:
            node_colors.append('lightgreen')  # Primarily a recipient
        else:
            node_colors.append('lightgray')  # Equal sending/receiving
    
    # Draw nodes
    nx.draw_networkx_nodes(graph, pos, node_size=800, alpha=0.8, node_color=node_colors)
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5, 
                          arrowsize=15, arrowstyle='->')
    
    # Create shortened labels for display
    labels = {}
    for node in graph.nodes():
        if '<' in node:
            name = node.split('<')[0].strip()
            email = node.split('<')[1].split('>')[0]
            # Use name if available, otherwise use email username
            if name:
                short_name = name
            else:
                short_name = email.split('@')[0]
            labels[node] = short_name
        else:
            # Just show the username part of the email
            labels[node] = node.split('@')[0]
    
    # Draw labels
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10)
    
    plt.title("Email Communication Network", fontsize=16)
    plt.axis('off')
    
    # Add a legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='Primarily Sender'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='Primarily Recipient'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgray', markersize=10, label='Both Sender/Recipient')
    ]
    plt.legend(handles=legend_elements, loc='lower right')
    
    # Save figure if output file is specified
    if output_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=300)
        logger.info(f"Saved social graph visualization to {output_file}")
    
    plt.show()

def analyze_network(graph):
    """
    Analyze the email network and return key statistics.
    
    Args:
        graph (networkx.Graph): The social graph to analyze
        
    Returns:
        dict: Network statistics
    """
    logger.info("Analyzing email network")
    
    # Calculate basic statistics
    stats = {
        'nodes': graph.number_of_nodes(),
        'edges': graph.number_of_edges(),
    }
    
    # Calculate degree statistics (who sends/receives the most)
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    
    # Top recipients (highest in-degree)
    top_recipients = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Top senders (highest out-degree)
    top_senders = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    
    stats['top_recipients'] = top_recipients
    stats['top_senders'] = top_senders
    
    # Calculate betweenness centrality (who bridges communities)
    try:
        centrality = nx.betweenness_centrality(graph)
        stats['key_connectors'] = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    except:
        stats['key_connectors'] = []
        logger.warning("Could not calculate betweenness centrality")
        
    return stats