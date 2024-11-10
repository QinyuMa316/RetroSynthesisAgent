

import json

from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.knowledgegraph import KnowledgeGraph


if __name__ == '__main__':

    material = 'Polyimide'
    pdf_folder_name = 'literature_pdfs_' + material
    result_folder_name = 'results_' + material
    result_json_name = 'gpt_results_40'
    modified_results_filepath = result_folder_name + '/' + result_json_name + '_modified.json'
    # origin tree without expansion
    with open(modified_results_filepath, 'r') as file:
        results_dict = json.load(file)
    # print(results_dict)
    tree = Tree(material.lower(), result_dict=results_dict)
    print('start construct tree...')
    result = tree.construct_tree()

    treeloader = TreeLoader()
    tree_filename = material + '_wo_exp.pkl'
    treeloader.save_tree(tree, tree_filename)

    img_suffix = '_40_modified'

    reactions_tree2 = tree.show_tree(view=False, simple=False, img_suffix=img_suffix)

    all_path = tree.find_all_paths()
    print(f'{len(all_path)} paths in this tree')

    reactions = tree.reactions
    kg = KnowledgeGraph(reactions)
    # kg.visualize_kg(html_name=f"KG_{material}.html")
    node_count = kg.G.number_of_nodes()
    print(f'{node_count} nodes in KnowledgeGraph')

    # 112 paths in this tree
    # 259 nodes in KnowledgeGraph

    tree = treeloader.load_tree(tree_filename)

