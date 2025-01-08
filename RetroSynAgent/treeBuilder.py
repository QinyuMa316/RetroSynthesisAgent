import copy
import json
from graphviz import Digraph
import time
import pubchempy
import pickle
import os
import re
from collections import deque
class CommonSubstanceDB:
    def __init__(self):
        self.added_database = self.get_added_database()
        self.smiles_cache = self.load_dict_from_json("smiles_cache.json")
        self.common_sub_cache = self.load_dict_from_json("substance_query_result.json")

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
        added_database = set(emol_list) | set(polymers) | {"2-chlorotrifluoromethylbenzene"}
        return added_database

    def is_common_chemical(self, compound_name, max_retries=1, delay=1):
        compound_identifier = self.get_smiles_cached(compound_name)
        retries = 0
        while retries < max_retries:
            try:
                if compound_identifier in self.added_database:
                    print(f"{compound_identifier} query succeed in emol or added db")
                    return True
                compound = pubchempy.get_compounds(compound_identifier, 'smiles')
                if not compound:
                    compound = pubchempy.get_compounds(compound_identifier, 'name')
                if compound:
                    print(f"{compound_identifier} query succeed in pubchem")
                    return True
                return False
            except pubchempy.PubChemHTTPError as e:
                retries += 1
                time.sleep(delay)
            except Exception as e:
                print(f"other error: {e}")
        return False

    def get_smiles_cached(self, compound_name):
        if compound_name in self.smiles_cache:
            return self.smiles_cache[compound_name]
        smiles = self.get_smiles_from_name(compound_name)
        self.smiles_cache[compound_name] = smiles
        self.save_dict_as_json(self.smiles_cache, "smiles_cache.json")
        return smiles

    def is_common_chemical_cached(self, compound_name):
        if compound_name in self.common_sub_cache:
            return self.common_sub_cache[compound_name]
        result = self.is_common_chemical(compound_name)
        self.common_sub_cache[compound_name] = result
        self.save_dict_as_json(self.common_sub_cache)
        return result


    @staticmethod
    def get_smiles_from_name(identifier):
        smiles_pattern = re.compile(r'^[A-Za-z0-9@+\-#\(\)\\/\=\[\]\.%\:?]*$')
        if smiles_pattern.match(identifier):
            return identifier

        compounds = pubchempy.get_compounds(identifier, 'name')
        if compounds:
            return compounds[0].canonical_smiles
        else:
            return identifier

    def load_dict_from_json(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}

    def save_dict_as_json(self, dict_file, filename="substance_query_result.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dict_file, f, ensure_ascii=False, indent=4)

class Node:
    def __init__(self, substance, reactions, product_dict,
                 fathers_set=None, father=None, reaction_index=None,
                 reaction_line=None, cache_func=None, unexpandable_substances=None,
                 # smiles_converter=None
                 ):
        self.reaction_index = reaction_index
        self.substance = substance
        self.children = []
        self.fathers_set = fathers_set if fathers_set is not None else set()
        self.father = father
        self.reaction_line = reaction_line if reaction_line is not None else []
        self.is_leaf = False
        self.cache_func = cache_func
        self.reactions = reactions
        self.product_dict = product_dict
        self.unexpandable_substances = unexpandable_substances
        # self.smiles_converter = smiles_converter

    def add_child(self, substance: str, reaction_index: int):
        curr_child_fathers_set = copy.deepcopy(self.fathers_set)
        curr_child_fathers_set.add(self.substance)
        curr_child_reaction_line = copy.deepcopy(self.reaction_line) + [reaction_index]
        # child = Node(self.smiles_converter(substance),
        child = Node(substance,
                     self.reactions, self.product_dict,
                     fathers_set=curr_child_fathers_set,
                     father=self,
                     reaction_index=reaction_index,
                     reaction_line=curr_child_reaction_line,
                     cache_func=self.cache_func,
                     unexpandable_substances=self.unexpandable_substances,
                     # smiles_converter=self.smiles_converter
                     )
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
            print(f'{self.substance} query succeed.')
            # time.sleep(0.1)
            return True
        else:
            print(f'{self.substance} query failed.')
            # time.sleep(0.1)
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
                            # child.is_leaf = False
                            # continue
                        # (2) If the current child node cannot be expanded further (1 cannot be expanded to initial reactants 2 cannot be obtained through existing reactions)
                        # Recursively check if the current child can expand further
                        is_valid = child.expand()  # , init_reactants)
                        # Cannot expand
                        if not is_valid:
                            # self.remove_child_by_reaction(reaction_idx)
                            # break
                            child.is_leaf = False
                            continue

                # After checking all reactions that can produce the substance, if "1" all children are invalid (no valid child nodes), cannot synthesize this substance
                if len(self.children) == 0:
                    # self.visited_substances[self.substance] = False
                    return False
                # After checking all reactions that can produce the substance, if "2" there are valid child nodes, the current node can expand
                else:
                    # self.visited_substances[self.substance] = True
                    return True

class Tree:
    def __init__(self, target_substance, result_dict=None, reactions_txt=None, reactions=None):
        if reactions:
            self.reactions = reactions
        elif result_dict:
            self.reactions, self.reactions_txt = self.parse_results(result_dict)
        elif reactions_txt:
            self.reactions = self.parse_reactions_txt(reactions_txt)
        self.product_dict = self.get_product_dict(self.reactions)
        self.target_substance = target_substance
        self.reaction_infos = set()
        self.all_path = []
        self.db = CommonSubstanceDB()
        # self.chemical_cache = self.load_dict_from_json("substance_query_result.json")
        # self.smiles_cache = self.load_dict_from_json("smiles_cache.json")
        self.unexpandable_substances = set()
        self.root = Node(target_substance, self.reactions, self.product_dict,
                         cache_func=self.db.is_common_chemical_cached,
                         unexpandable_substances=self.unexpandable_substances,
                         # smiles_converter=self.db.get_smiles_cached
                         )

    def construct_tree(self):
        self.root.expand()
        return self.root

    def get_product_dict(self, reactions_dict):
        product_dict = {}
        for idx, entry in reactions_dict.items():
            products = entry['products']
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
        # for pdf_name, (reaction, property) in result_dict.items():
        for pdf_name, reaction in result_dict.items():
            reactions_txt_all += (reaction + '\n\n')

            additional_reactions, idx = self.parse_reactions(reaction, idx, pdf_name)
            reactions.update(additional_reactions)
        return reactions, reactions_txt_all


    # def is_common_chemical_cached(self, compound_name):
    #     if compound_name in self.chemical_cache:
    #         return self.chemical_cache[compound_name]
    #     result = self.db.is_common_chemical(compound_name)
    #     self.chemical_cache[compound_name] = result
    #     self.save_dict_as_json(self.chemical_cache)
    #     return result
    #
    # def get_smiles_cached(self, compound_name):
    #     if compound_name in self.smiles_cache:
    #         return self.smiles_cache[compound_name]
    #     smiles = self.db.get_smiles_from_name(compound_name)
    #     self.smiles_cache[compound_name] = smiles
    #     self.save_dict_as_json(self.smiles_cache, "smiles_cache.json")
    #     return smiles
    #
    # def load_dict_from_json(self, filename):
    #     if os.path.exists(filename):
    #         with open(filename, 'r', encoding='utf-8') as f:
    #             return json.load(f)
    #     else:
    #         return {}
    #
    # def save_dict_as_json(self, dict_file, filename="substance_query_result.json"):
    #     with open(filename, 'w', encoding='utf-8') as f:
    #         json.dump(dict_file, f, ensure_ascii=False, indent=4)

    def _count_nodes(self, node):
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def get_node_count(self):
        return self._count_nodes(self.root)

    def get_reactions_in_tree_(self, reaction_idx_list):
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


    def get_reactions_in_tree(self):
        """
        Traverse the retrosynthetic tree directly and collect all reactions involved.
        Returns a formatted string of all reactions in the tree.
        """
        reaction_idx_set = set()

        def traverse(node):
            if node.reaction_index is not None:
                reaction_idx_set.add(node.reaction_index)
            for child in node.children:
                traverse(child)

        traverse(self.root)
        reactions_tree = self.get_reactions_in_tree_(list(reaction_idx_set))
        return reactions_tree

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

    # def _collect_non_leaf_nodes(self, node):
    #     non_leaf_nodes = []
    #     if not node.is_leaf:
    #         non_leaf_nodes.append(node.substance)
    #     for child in node.children:
    #         non_leaf_nodes.extend(self._collect_non_leaf_nodes(child))
    #     return non_leaf_nodes
    #
    # def get_non_leaf_node_names(self):
    #     return self._collect_non_leaf_nodes(self.root)
    #
    # def _collect_leaf_nodes(self, node):
    #     leaf_nodes = []
    #     if node.is_leaf:
    #         leaf_nodes.append(node.substance)
    #     for child in node.children:
    #         leaf_nodes.extend(self._collect_leaf_nodes(child))
    #     return leaf_nodes
    #
    # def get_leaf_node_names(self):
    #     return self._collect_leaf_nodes(self.root)

    # ======================================================================
    #
    # def add_nodes_edges(self, node, dot=None, simple = False):
    #     # If it is the root node
    #     if dot is None:
    #         if len(node.children) == 0:
    #             raise Exception("Empty tree!")
    #         # dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000'})
    #         dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000', 'splines': 'true'})
    #
    #         # lightblue2
    #         dot.attr('node', shape='ellipse', style='filled', color='lightblue2', fontname="Arial", fontsize="8")
    #         dot.attr('edge', color='gray', fontname="Arial", fontsize="8")
    #         if simple:
    #             dot.node(name=self.get_name(node), label='', width='0.1', height='0.1')
    #         else:
    #             dot.node(name=self.get_name(node), label=node.substance)
    #
    #     for child in node.children:
    #         if simple:
    #             dot.node(name=self.get_name(child), label='', width='0.1', height='0.1')
    #             dot.edge(self.get_name(node), self.get_name(child), label='', arrowhead='none')
    #         else:
    #             dot.node(name=self.get_name(child), label=child.substance, width='0.1', height='0.1')
    #             dot.edge(self.get_name(node), self.get_name(child), label=f"idx : {str(child.reaction_index)}", arrowhead='none')
    #
    #         dot = self.add_nodes_edges(child, dot=dot, simple=simple)
    #         # reaction_info = f"reaction idx: {str(child.reaction_index)}, conditions: {self.reactions[child.reaction_index]['conditions']}"
    #         reaction_info = str(child.reaction_index)
    #         self.reaction_infos.add(reaction_info)
    #     return dot

    # def sanitize_name(self, name):
    #     """
    #     Replace hyphens and other special characters with underscores to create Graphviz-friendly identifiers.
    #     """
    #     # Replace hyphens and spaces with underscores
    #     sanitized = name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '').replace('[', '').replace(
    #         ']', '').replace('{', '').replace('}', '').replace(',', '').replace("'", "").replace('"', '').replace('.',                                                                                                   '_')
    #     return sanitized
    #
    # def get_name(self, node):
    #     if node.reaction_index is None:
    #         return self.sanitize_name(node.substance)  # **MODIFIED**
    #     else:
    #         depth = str(len(node.fathers_set))
    #         sanitized_substance = self.sanitize_name(node.substance)  # **MODIFIED**
    #         reaction_line = '.'.join(map(str, list(node.reaction_line)))
    #         sanitized_reaction_line = self.sanitize_name(reaction_line)  # **MODIFIED**
    #         return f"{depth}_{sanitized_substance}_{sanitized_reaction_line}"  # **MODIFIED**
    #
    # def get_name_level_order(self, node):
    #     if node.reaction_index is None:
    #         return self.sanitize_name(node.substance)  # **MODIFIED**
    #     else:
    #         depth = str(len(node.fathers_set))
    #         sanitized_substance = self.sanitize_name(node.substance)  # **MODIFIED**
    #         sanitized_father = self.sanitize_name(node.father.substance)  # **MODIFIED**
    #         return f"{depth}_{sanitized_substance}_{sanitized_father}"  # **MODIFIED**
    #
    # def add_nodes_edges_level_order(self, node, dot=None, simple=False):
    #     # If it is the root node
    #     if dot is None:
    #         if len(node.children) == 0:
    #             raise Exception("Empty tree!")
    #         dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR'})
    #         # dot.attr(overlap='false', ranksep='0.5', nodesep='1')
    #         dot.attr('node', shape='ellipse', style='filled', fillcolor='#82b0d2', color='#999999', fontname="Arial", fontsize="8")
    #         dot.attr('edge', color='#999999', fontname="Arial", fontsize="8")
    #         root_fillcolor = '#beb8dc' # 紫色
    #         dot.node(name=self.get_name_level_order(node), label='' if simple else node.substance, width='0.1', height='0.1', fillcolor=root_fillcolor)
    #
    #     queue = deque([node])
    #     while queue:
    #         level_nodes = []
    #         level_edges = []
    #         for _ in range(len(queue)):
    #             cur_node = queue.popleft()
    #             if cur_node.reaction_index is not None:
    #                 edge_name = (self.get_name_level_order(cur_node.father) + self.get_name_level_order(cur_node))
    #                 # 遍历每层节点，如果未添加则添加
    #                 if edge_name not in level_edges:
    #                     # label=f"idx : {str(cur_node.reaction_index)}"
    #                     dot.edge(self.get_name_level_order(cur_node.father), self.get_name_level_order(cur_node), label=f"", arrowhead='none')
    #                     level_edges.append(edge_name)
    #
    #                     reaction_info = str(cur_node.reaction_index)
    #                     self.reaction_infos.add(reaction_info)
    #
    #                 # 判断当前节点是否为叶子节点
    #                 node_name = cur_node.substance
    #                 node_color = '#8ecfc9' if cur_node.is_leaf else '#82b0d2'  # 根据条件设定颜色
    #                 if node_name not in level_nodes:
    #                     dot.node(name=self.get_name_level_order(cur_node), label='' if simple else cur_node.substance, width='0.1', height='0.1', fillcolor=node_color)
    #                     level_nodes.append(node_name)
    #
    #             for child in cur_node.children:
    #                 queue.append(child)
    #     return dot
    #
    #
    # def show_tree(self, view=False, simple=False, dpi='500', img_suffix = ''):
    #     dot = self.add_nodes_edges_level_order(self.root, simple=simple)
    #     dot.attr(dpi=dpi)
    #     dot.render(filename=str(self.target_substance) + img_suffix, format='png', view=view)

    # ======================================================================


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
