import json
import networkx as nx
from pyvis.network import Network
import warnings
warnings.filterwarnings('ignore')

class KnowledgeGraph:
    def __init__(self, reactions, properties=None):
        self.properties = properties if properties is not None else {}
        self.reactions = reactions
        self.G = nx.DiGraph()  # Initialize directed graph
        self.chemical_substances = set()  # Set of chemical substances
        self._build_kg()  # Automatically build the knowledge graph

    def _build_kg(self):
        # Process the properties part
        for substance, prop_dict in self.properties.items():
            self.chemical_substances.add(substance)
            for prop_name, prop_value in prop_dict.items():
                self.G.add_node(substance)  # Add substance node
                self.G.add_node(prop_value)  # Add value node
                self.G.add_edge(substance, prop_value, label=prop_name)  # Add property edge

        # Process the reactions part
        for idx, reaction in self.reactions.items():
            reactants = reaction["reactants"]
            products = reaction["products"]
            # conditions = reaction["conditions"]

            self.chemical_substances.update(reactants)
            self.chemical_substances.update(products)

            for reactant in reactants:
                for product in products:
                    self.G.add_node(reactant)  # Add reactant node
                    self.G.add_node(product)  # Add product node
                    self.G.add_edge(reactant, product, label=f"reaction idx: {idx}")  # Add reaction edge
                    # label: conditions -> idx

    def export_to_json(self, file_path):
        # Create nodes with unique ids
        node_mapping = {node: idx + 1 for idx, node in enumerate(self.G.nodes)}
        nodes = [{"id": node_mapping[node], "name": node} for node in self.G.nodes]

        # Create links
        links = [
            {"source": node_mapping[edge[0]], "target": node_mapping[edge[1]]}
            for edge in self.G.edges
        ]

        # Combine into final JSON structure
        graph_data = {
            "nodes": nodes,
            "links": links
        }

        # Save to file
        with open(file_path, "w") as f:
            json.dump(graph_data, f, indent=4)

    def count_nodes(self):
        return self.G.number_of_nodes()

    def visualize_kg(self, html_name="KG.html"):
        net = Network(notebook=True, height="750px", width="100%", directed=True)

        # add nodes & edges
        for node in self.G.nodes:

            if node in self.chemical_substances:
                net.add_node(node, label=node, shape="circle", color={
                    'background': 'pink',
                    'border': 'gray',
                    'highlight': {
                        'border': 'gray',
                        'background': 'pink'
                    }
                }, borderWidth=1, font={'size': 10}, title=f"{node}")
                # Chemical Substance: {node}
            else:
                net.add_node(node, label=node, shape="circle", color={
                    'background': 'lightblue',
                    'border': 'gray',
                    'highlight': {
                        'border': 'gray',
                        'background': 'lightblue'
                    }
                }, borderWidth=1, font={'size': 10}, title=f"{node}")

        for edge in self.G.edges(data=True):
            source, target, data = edge
            label = data['label']
            net.add_edge(source, target, label=label, color='gray')

        net.set_options("""
        var options = {
          "physics": {
            "repulsion": {
              "centralGravity": 0.0,
              "springLength": 200,
              "springConstant": 0.05,
              "nodeDistance": 200,
              "damping": 0.09
            },
            "minVelocity": 0.75
          }
        }
        """)
        net.show(html_name)
