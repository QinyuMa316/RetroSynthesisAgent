
import os
import json
from RetroSynAgent.GPTAPI import GPTAPI
from RetroSynAgent import prompts
from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.knowledgegraph import KnowledgeGraph


if __name__ == '__main__':

    material = 'Polyimide'
    pdf_folder_name = 'literature_pdfs_' + material
    result_folder_name = 'results_' + material
    result_json_name = 'gpt_results_40'
    modified_results_filepath = result_folder_name + '/' + result_json_name + '_modified.json'

    # note: 1. substance name consistency in different literatures
    if not os.path.exists(modified_results_filepath):
        with open(result_folder_name+'/'+result_json_name+'.json', 'r') as file:
            results_dict = json.load(file)
            print('load original results data, starting modifying ...')
        count = 1
        for key, values in results_dict.items():
            # count += 1
            # if count >= 20:
            reactions_txt = values[0]
            prompt = prompts.prompt_unify_name.format(substance=material, reactions=reactions_txt)
            print(f'===== origin txt:\n{reactions_txt}\n')
            llm = GPTAPI()
            reactions_txt_modified = llm.answer_wo_vision(prompt)
            values[0] = reactions_txt_modified
            print(f'===== modified txt:\n{reactions_txt_modified}\n')

        with open(result_folder_name+'/'+result_json_name+'_modified.json', 'w') as file:
            json.dump(results_dict, file, indent=4)
    else:
        with open(modified_results_filepath, 'r') as file:
            results_dict = json.load(file)
            print('load modified results data')

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

