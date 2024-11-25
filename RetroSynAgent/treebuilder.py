import copy
import json
from graphviz import Digraph
import time
import pubchempy
import pickle
import base64
from io import BytesIO
from PIL import Image
import os
from collections import deque

class CommonSubstanceDB:
    def __init__(self):
        self.added_database = self.get_added_database()
    @staticmethod
    def read_data_from_json(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def get_added_database(self):
        polymers = [
            "Polyethylene",
            "Polypropylene",
            "Polystyrene",
            "Polyvinyl chloride",
            "Polyethylene terephthalate",
            "Polytetrafluoroethylene",
            "Polycarbonate",
            "Poly(methyl methacrylate)",
            "Polyurethane",
            "Polyamide",
            "Polyvinyl acetate",
            "Polybutadiene",
            "Polychloroprene",
            "Poly(acrylonitrile-butadiene-styrene)",
            "Polyoxymethylene",
            "Polylactic acid",
            "Polyethylene glycol",
            "Poly(vinyl alcohol)",
            "Polyacrylamide",
            "Polyethylene oxide",
            "Poly(ethylene-co-vinyl acetate)"
        ]

        polymers = [polymer.lower() for polymer in polymers]
        emol_list = self.read_data_from_json('RetroSynAgent/emol.json')
        added_database = set(emol_list) | {"CCl2"} | set(polymers)
        return added_database

    def is_common_chemical(self, compound_name, max_retries=1, delay=1):
        """
        Query the PubChem database to determine if a compound is common; retry on error.
        :param compound_identifier: The compound's SMILES, English name, or other identifier (string)
        :param max_retries: Maximum number of retries
        :param delay: Wait time between retries (seconds)
        :return: Returns True if a relevant record is found, otherwise returns False
        """
        compound_identifier = self.get_smiles_from_name(compound_name)
        retries = 0
        while retries < max_retries:
            try:
                if compound_identifier in self.added_database:
                    print(f"{compound_identifier} query success")
                    return True
                # Query the compound by SMILES
                compound = pubchempy.get_compounds(compound_identifier, 'smiles')
                if not compound:
                    # If SMILES query fails, try querying by name
                    compound = pubchempy.get_compounds(compound_identifier, 'name')
                if compound:
                    print(f"{compound_identifier} query succeed")
                    return True
                return False
            except pubchempy.PubChemHTTPError as e:
                # print(f"{compound_identifier} query failed: {e}. Retrying... ({retries + 1}/{max_retries})")
                retries += 1
                time.sleep(delay)
            except Exception as e:
                print(f"other error: {e}")
                # Other error: <urlopen error [Errno 54] Connection reset by peer>
        print(f"{compound_identifier} query failed")  # Maximum number of retries reached
        return False

    @staticmethod
    def get_smiles_from_name(compound_name):
        compounds = pubchempy.get_compounds(compound_name, 'name')
        if compounds:
            return compounds[0].canonical_smiles
        else:
            return compound_name

class Node:
    def __init__(self, substance, reactions, product_dict,
                 fathers_set=None, father=None, reaction_index=None,
                 reaction_line=None, cache_func=None, unexpandable_substances=None):  # , visited_substances=None):
        '''
        reaction_index: Index of the reaction that produces the substance: idx (str)
        substance: The name of the current node: name (str)
        children: List of child nodes: [Node, ...]
        fathers_set: Set of parent node names: set(name (str), name (str))
        reaction_line: Reaction path: [idx (str), ...]
        brothers: Sibling nodes: [None, ...]
        '''
        self.reaction_index = reaction_index
        self.substance = substance
        self.children = []
        self.fathers_set = fathers_set if fathers_set is not None else set()
        self.father = father  # father_node
        self.reaction_line = reaction_line if reaction_line is not None else []
        self.is_leaf = False
        self.cache_func = cache_func  # Add caching function
        self.reactions = reactions
        self.product_dict = product_dict
        self.unexpandable_substances = unexpandable_substances
        # self.visited_substances = visited_substances

    def add_child(self, substance: str, reaction_index: int):
        '''
        Add a child node to the current node (self) in self.children
        child: The name of the current child node: substance
        Current child's parent set: curr_child_fathers_set = Current node (current child's parent) self + current node's parent set
        Current child's reaction path: curr_child_reaction_line = idx from current node to current child + current node's reaction path
        '''
        curr_child_fathers_set = copy.deepcopy(self.fathers_set)
        curr_child_fathers_set.add(self.substance)
        curr_child_reaction_line = copy.deepcopy(self.reaction_line) + [reaction_index]
        child = Node(substance, self.reactions, self.product_dict,
                     fathers_set=curr_child_fathers_set,
                     father=self,
                     reaction_index=reaction_index,
                     reaction_line=curr_child_reaction_line,
                     cache_func=self.cache_func,
                     unexpandable_substances=self.unexpandable_substances,
                     # visited_substances = self.visited_substances
                     )  # Pass caching function
        self.children.append(child)
        return child

    def remove_child_by_reaction(self, reaction_index: int):
        """
        Remove children with the same reaction as ancestor nodes (forming a loop)
        This not only deletes the current child node but also deletes sibling nodes with the same reaction (same reaction index)
        """
        self.children = [child for child in self.children if child.reaction_index != reaction_index]

    def expand(self) -> bool:
        """
        reactions {'idx': {'reactants':[], 'products':[], conditions: ''}, ...}
        product_dict {'product': [idx1, idx2, ...], ...}
        """
        # Base conditions:
        # The reactant already belongs to existing reactants, no need to expand further
        # if self.substance in init_reactants:
        if self.cache_func(self.substance):
            self.is_leaf = True
            # self.visited_substances[self.substance] = True
            # print(f"{self.substance} is accessible")
            return True
        else:
            reactions_idxs = self.product_dict.get(self.substance, [])
            # The substance cannot be obtained through existing reactions
            if len(reactions_idxs) == 0:
                self.unexpandable_substances.add(self.substance)
                # self.visited_substances[self.substance] = False
                # print(f"{self.substance} cannot be expanded further")
                return False
            # The substance is not among existing reactants but can be obtained through existing reactions
            else:
                # Iterate over all reactions that can produce the substance
                for reaction_idx in reactions_idxs:
                    # Get the reactants for the reaction that produces the substance, iterate and add as child nodes of the current node
                    reactants_list = self.reactions[reaction_idx]['reactants']  # ['reactions'][0]
                    # Generate all reactants for the current node substance
                    for reactant in reactants_list:
                        # 1 === self.add_child includes: creating the current child node and adding it to self.children.append(child)
                        child = self.add_child(reactant, reaction_idx)
                        # 2 === Check if the current child node is valid
                        # (1) If the current child node has the same name as ancestor nodes (forming a loop), it is invalid
                        # (self.remove_child_by_reaction not only removes the current child node but also nodes with the same reaction index)
                        if child.substance in child.fathers_set:
                            self.remove_child_by_reaction(reaction_idx)
                            break
                        # (2) If the current child node cannot be expanded further (1 cannot be expanded to initial reactants 2 cannot be obtained through existing reactions)
                        # Recursively check if the current child can expand further
                        is_valid = child.expand()  # , init_reactants)
                        # Cannot expand
                        if not is_valid:
                            self.remove_child_by_reaction(reaction_idx)
                            break
                # After checking all reactions that can produce the substance, if "1" all children are invalid (no valid child nodes), cannot synthesize this substance
                if len(self.children) == 0:
                    # self.visited_substances[self.substance] = False
                    return False
                # After checking all reactions that can produce the substance, if "2" there are valid child nodes, the current node can expand
                else:
                    # self.visited_substances[self.substance] = True
                    return True


# retrosynthetic Tree, contains all substance nodes
class Tree:
    def __init__(self, target_substance, result_dict=None, reactions_txt=None):
        """
        reactions_dict[str(idx)] = {
            'reactants': tuple(reactants),
            'products': tuple(products),
            'conditions': conditions, }
        """
        if result_dict:
            self.reactions, self.reactions_txt = self.parse_results(result_dict)
        elif reactions_txt:
            self.reactions = self.parse_reactions_txt(reactions_txt)
        # self.reactions = self.parse_reactions(reactions_txt)
        self.product_dict = self.get_product_dict(self.reactions)
        self.target_substance = target_substance
        # self.root = Node(target_substance)
        self.reaction_infos = set()
        self.all_path = []
        self.chemical_cache = self.load_dict_from_json()  # Used to record whether a substance can be queried in the database
        self.unexpandable_substances = set()  # Set of nodes that cannot be expanded
        # self.visited_substances = {}  # Records the substances visited and their expansion results
        # Create the root node and pass the cache query method, and the set of non-expandable nodes
        self.root = Node(target_substance, self.reactions, self.product_dict,
                         cache_func=self.is_common_chemical_cached,
                         unexpandable_substances=self.unexpandable_substances,
                         # visited_substances = self.visited_substances
                         )

    def get_product_dict(self, reactions_dict):
        '''
        reactions_dict[str(idx)] = {
            'reactants': tuple(reactants),
            'products': tuple(products),
            'conditions': conditions,
        }
        '''
        product_dict = {}
        # Iterate over reactions_entry dictionary
        for idx, entry in reactions_dict.items():
            products = entry['products']
            # Iterate over products
            for product in products:
                product = product.strip()
                if product not in product_dict:
                    product_dict[product] = []
                product_dict[product].append(idx)

        for key, value in product_dict.items():
            product_dict[key] = tuple(value)
        return product_dict

    def parse_reactions_txt(self, reactions_txt):
        # idx = 1
        # note: v13 adds parsing of Conditions in reaction_txt & retains original Reaction idx instead of re-labeling
        reactants = []
        products = []
        reactions_dict = {}
        lines = reactions_txt.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('Reaction idx:'):
                idx = line.split("Reaction idx:")[1].strip()
            if line.startswith("Reactants:"):
                reactants = line.split("Reactants:")[1].strip().split(', ')
                reactants = [reactant.lower() for reactant in reactants]
            elif line.startswith("Products:"):
                products = line.split("Products:")[1].strip().split(', ')
                products = [product.lower() for product in products]
            elif line.startswith("Conditions:"):
                conditions = line.split("Conditions:")[1].strip()
            elif line.startswith("Source:"):
                source = line.split("Source:")[1].strip()
                reactions_dict[str(idx)] = {
                    'reactants': tuple(reactants),
                    'products': tuple(products),
                    'conditions': conditions,
                    'source': source,
                }
                # idx += 1
        return reactions_dict

    def parse_reactions(self, reactions_txt, idx, pdf_name):
        # idx = 1
        reactants = []
        products = []
        reactions_dict = {}
        lines = reactions_txt.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Reactants:"):
                reactants = line.split("Reactants:")[1].strip().split(', ')
                reactants = [reactant.lower() for reactant in reactants]
            elif line.startswith("Products:"):
                products = line.split("Products:")[1].strip().split(', ')
                products = [product.lower() for product in products]
            elif line.startswith("Conditions:"):
                conditions = line.split("Conditions:")[1].strip()
                reactions_dict[str(idx)] = {
                    'reactants': tuple(reactants),
                    'products': tuple(products),
                    'conditions': conditions,
                    'source': pdf_name,
                }
                idx += 1
        return reactions_dict, idx

    def parse_results(self, result_dict):
        """
        result_dict : gpt_results_40.json
        """
        reactions_txt_all = ''
        reactions = {}
        idx = 1
        for pdf_name, (reaction, property) in result_dict.items():
            reactions_txt_all += (reaction + '\n\n')
            additional_reactions, idx = self.parse_reactions(reaction, idx, pdf_name)
            reactions.update(additional_reactions)
        return reactions, reactions_txt_all


    def save_dict_as_json(self, dict_file, filename="substance_query_result.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dict_file, f, ensure_ascii=False, indent=4)

    def load_dict_from_json(self, filename="substance_query_result.json"):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                dict_file = json.load(f)
                return dict_file
        else:
            return {}

    def is_common_chemical_cached(self, compound_name):
        """Use cache to avoid redundant compound queries"""
        if compound_name in self.chemical_cache:
            return self.chemical_cache[compound_name]
        db = CommonSubstanceDB()
        result = db.is_common_chemical(compound_name)
        self.chemical_cache[compound_name] = result
        self.save_dict_as_json(self.chemical_cache)
        return result

    def construct_tree(self): # , init_reactants):
        # global init_reactants
        # if self.root.substance in init_reactants:
        #     raise ValueError("Target substance is already in initial reactants.")

        if self.is_common_chemical_cached(self.root.substance):
            raise ValueError("Target substance is easily gotten.")
            # return ("Target substance is easily gotten.")
        result = self.root.expand() #, init_reactants)
        if result:
            return True # "Build tree successfully!"
        else:
            return False # "Failed to build tree."

    def get_name(self, node):
        # If it is the root node
        if node.reaction_index is None:
            return node.substance
        else:
            depth = str(len(node.fathers_set))
            return (depth+ "-" + node.substance+ "-" + '.'.join(map(str, list(node.reaction_line))))

    def add_nodes_edges(self, node, dot=None, simple = False):
        # If it is the root node
        if dot is None:
            if len(node.children) == 0:
                raise Exception("Empty tree!")
            # dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000'})
            dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000', 'splines': 'true'})

            # lightblue2
            dot.attr('node', shape='ellipse', style='filled', color='lightblue2', fontname="Arial", fontsize="8")
            dot.attr('edge', color='gray', fontname="Arial", fontsize="8")
            if simple:
                dot.node(name=self.get_name(node), label='', width='0.1', height='0.1')
            else:
                dot.node(name=self.get_name(node), label=node.substance)

        for child in node.children:
            if simple:
                dot.node(name=self.get_name(child), label='', width='0.1', height='0.1')
                dot.edge(self.get_name(node), self.get_name(child), label='', arrowhead='none')
            else:
                dot.node(name=self.get_name(child), label=child.substance, width='0.1', height='0.1')
                dot.edge(self.get_name(node), self.get_name(child), label=f"idx : {str(child.reaction_index)}", arrowhead='none')

            dot = self.add_nodes_edges(child, dot=dot, simple=simple)
            # reaction_info = f"reaction idx: {str(child.reaction_index)}, conditions: {self.reactions[child.reaction_index]['conditions']}"
            reaction_info = str(child.reaction_index)
            self.reaction_infos.add(reaction_info)
        return dot

    def get_name_level_order(self, node):
        if node.reaction_index is None:
            return node.substance
        else:
            depth = str(len(node.fathers_set))
            # note: v13 return f"{depth}-{node.substance}" -> f"{depth}-{node.substance}-{node.father.node}"
            return f"{depth}-{node.substance}-{node.father.substance}"

    def add_nodes_edges_level_order2(self, node, dot=None, simple=False):
        # If it is the root node
        if dot is None:
            if len(node.children) == 0:
                raise Exception("Empty tree!")
            dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR'})
            # dot.attr(overlap='false', ranksep='0.5', nodesep='1')
            dot.attr('node', shape='ellipse', style='filled', fillcolor='#82b0d2', color='#999999', fontname="Arial", fontsize="8")
            dot.attr('edge', color='#999999', fontname="Arial", fontsize="8")
            root_fillcolor = '#beb8dc' # 紫色
            dot.node(name=self.get_name_level_order(node), label='' if simple else node.substance, width='0.1', height='0.1', fillcolor=root_fillcolor)

        queue = deque([node])
        while queue:
            level_nodes = []
            level_edges = []
            for _ in range(len(queue)):
                cur_node = queue.popleft()
                if cur_node.reaction_index is not None:
                    edge_name = (self.get_name_level_order(cur_node.father) + self.get_name_level_order(cur_node))
                    # 遍历每层节点，如果未添加则添加
                    if edge_name not in level_edges:
                        # label=f"idx : {str(cur_node.reaction_index)}"
                        dot.edge(self.get_name_level_order(cur_node.father), self.get_name_level_order(cur_node), label=f"", arrowhead='none')
                        level_edges.append(edge_name)

                        reaction_info = str(cur_node.reaction_index)
                        self.reaction_infos.add(reaction_info)

                    # 判断当前节点是否为叶子节点
                    node_name = cur_node.substance
                    node_color = '#8ecfc9' if cur_node.is_leaf else '#82b0d2'  # 根据条件设定颜色
                    if node_name not in level_nodes:
                        dot.node(name=self.get_name_level_order(cur_node), label='' if simple else cur_node.substance, width='0.1', height='0.1', fillcolor=node_color)
                        level_nodes.append(node_name)

                for child in cur_node.children:
                    queue.append(child)
        return dot

    def get_reactions_in_tree(self, reaction_idx_list):
        reactions_tree = ''
        for idx in reaction_idx_list:
            reactants = self.reactions[idx]['reactants']
            products = self.reactions[idx]['products']
            conditions = self.reactions[idx]['conditions']
            source = self.reactions[idx]['source']
            reaction_string = (f"Reaction idx: {idx}\nReactants: {', '.join(reactants)}\nProducts: {', '.join(products)}\n"
                               f"Conditions: {conditions}\nSource: {source}\n\n")
            reactions_tree += reaction_string
        return reactions_tree


    def show_tree(self, view=False, simple=False, dpi='500', img_suffix=''):

        dot = self.add_nodes_edges_level_order2(self.root, simple=simple)
        dot.attr(dpi=dpi)
        dot.render(filename=str(self.target_substance) + img_suffix, format='png', view=view)
        # tree_base64_image = self.png_to_base64(str(self.target_substance) + img_suffix + '.png')

        # dot.render('substances_tree', format='svg', view=True)

        # Extract the relevant reactions from all_reactions_txt based on the idx involved in the tree
        # reactions_tree: all reactions(idx, reactants, products, conditions) in the tree
        reaction_idx_list = list(self.reaction_infos)
        reactions_tree = self.get_reactions_in_tree(reaction_idx_list)
        return reactions_tree #, tree_base64_image


    def png_to_base64(self, png_path):
        # Open the PNG image file
        with Image.open(png_path) as image:
            # Create a byte stream object
            buffered = BytesIO()
            # Save the image to the byte stream in PNG format
            image.save(buffered, format="PNG")
            # Get the binary content of the byte stream and encode it as Base64
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return base64_image


    def find_all_paths(self):
        """
        class Node:
        def __init__(self, substance, fathers_set=None, reaction_index=None, reaction_line=None):
        # reaction_index: the index of the reaction obtained from the nth reaction: idx(str)
        # substance: the name of the current node: name(str)
        # children: list of child nodes: [Node, ...]
        # fathers_set: set of parent node names: set(name(str), name(str))
        # reaction_line: reaction path: [idx(str), ...]
        # brothers: list of sibling nodes: [None, ...]
        self.reaction_index = reaction_index
        self.substance = substance
        self.children = []
        self.fathers_set = fathers_set if fathers_set is not None else set()
        self.reaction_line = reaction_line if reaction_line is not None else []
        """
        path = self.search_reaction_pathways(self.root)
        path = self.clean_path(path)
        path = self.remove_supersets(path)
        return path

    def search_reaction_pathways(self, node):
        # Termination condition: if it is a leaf node, return an empty path
        if node.is_leaf:
            return [[]]

        # Store the set of paths for each reaction index
        reaction_paths = {}

        for child in node.children:
            paths = self.search_reaction_pathways(child)  # Recursively retrieve paths from child nodes
            reaction_idx = child.reaction_index

            # If the reaction index does not exist yet or the current path set is empty, directly overwrite it
            if reaction_idx not in reaction_paths or reaction_paths[reaction_idx] == [[]]:
                reaction_paths[reaction_idx] = paths
            elif paths:  # If the child node has valid paths
                # Combine the existing paths with the new paths
                combined_paths = []
                for prev_path in reaction_paths[reaction_idx]:
                    for curr_path in paths:
                        combined_paths.append(prev_path + curr_path)
                reaction_paths[reaction_idx] = combined_paths

        # Aggregate all reaction paths
        pathways = []
        for reaction_idx, paths in reaction_paths.items():
            for path in paths:
                pathways.append([reaction_idx] + path)
        return pathways


    def clean_path(self, all_path):
        # Deduplication function
        def remove_duplicates(lst):
            seen = set()
            return [x for x in lst if x not in seen and not seen.add(x)]

        # Deduplicate each sublist
        result = [remove_duplicates(sublist) for sublist in all_path]
        return result

    def remove_supersets(self, data):
        """
            Remove larger sets that contain smaller sets, keeping the smaller sets
            :param data: List of lists, the original data
            :return: The result list after removing larger sets that contain other sets
        """
        # Convert to list of sets to facilitate subset checking
        data_sets = [set(sublist) for sublist in data]

        # Result list to store the kept subsets
        result = []

        # Iterate over all the sets
        for i, current_set in enumerate(data_sets):
            # Check if the current set is a superset of any other set
            is_superset = False
            for j, other_set in enumerate(data_sets):
                if i != j and current_set.issuperset(other_set):
                    is_superset = True
                    break
            # If the current set is not a superset of any other, keep it
            if not is_superset:
                result.append(data[i])

        return result


class TreeLoader():
    def save_tree(self, tree, filename):
        with open(filename, 'wb') as f:
            pickle.dump(tree, f)
        print(f"Tree saved to {filename}")

    def load_tree(self, filename):
        with open(filename, 'rb') as f:
            tree = pickle.load(f)
        print(f"Tree loaded from {filename}")
        return tree
