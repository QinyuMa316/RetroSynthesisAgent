import json
from RetroSynAgent.treeBuilder import Tree, TreeLoader
from RetroSynAgent.pdfProcessor import PDFProcessor
from RetroSynAgent.knowledgeGraph import KnowledgeGraph
from RetroSynAgent import prompts
from RetroSynAgent.GPTAPI import GPTAPI
from RetroSynAgent.pdfDownloader import PDFDownloader
import fitz  # PyMuPDF
import os
import json
import re
import pubchempy
from RetroSynAgent.entityAlignment import EntityAlignment
from RetroSynAgent.treeExpansion import TreeExpansion
from RetroSynAgent.reactionsFiltration import ReactionsFiltration
import argparse

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Process PDFs and extract reactions.")
    parser.add_argument('--material', type=str, required=True,
                        help="Material name for processing.")
    parser.add_argument('--num_results', type=int, required=True,
                        help="Number of PDF to download.")
    parser.add_argument('--alignment', type=str, default="False", choices=["True", "False"],
                        help="Whether to align entities except for root node.")
    parser.add_argument('--expansion', type=str, default="False", choices=["True", "False"],
                        help="Whether to expand the tree with additional literature.")
    parser.add_argument('--filtration', type=str, default="False", choices=["True", "False"],
                        help="Whether to filter reactions.")
    return parser.parse_args()

def countNodes(tree):
    node_count = tree.get_node_count()
    return node_count

def searchPathways(tree):
    all_path = tree.find_all_paths()
    return all_path


def recommendReactions(prompt, result_folder_name, response_name):
    res = GPTAPI().answer_wo_vision(prompt)
    with open(f'{result_folder_name}/{response_name}.txt', 'w') as f:
        f.write(res)
    start_idx = res.find("Recommended Reaction Pathway:")
    recommend_reactions_txt = res[start_idx:]
    print(f'\n=================================================='
          f'==========\n{recommend_reactions_txt}\n====================='
          f'=======================================\n')
    return recommend_reactions_txt

def main():
    # material = 'Polyimide'
    # num_results = 10
    # alignment = True
    # expansion = True
    # filtration = False

    # Parse command-line arguments
    args = parse_arguments()
    material = args.material
    num_results = args.num_results
    # turn str to bool
    alignment = args.alignment == "True"
    expansion = args.alignment == "True"
    filtration = args.filtration == "True"

    pdf_folder_name = 'pdf_pi'
    result_folder_name = 'res_pi'
    result_json_name = 'llm_res'
    tree_folder_name = 'tree_pi'
    os.makedirs(tree_folder_name, exist_ok=True)
    entityalignment = EntityAlignment()
    treeloader = TreeLoader()
    tree_expansion = TreeExpansion()
    reactions_filtration = ReactionsFiltration()

    ### extractInfos

    # 1  query literatures & download
    downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name, num_results=num_results, n_thread=3)
    pdf_name_list = downloader.main()
    print(f'successfully downloaded {len(pdf_name_list)} pdfs for {material}')

    # 2 Extract infos from PDF about reactions
    pdf_processor = PDFProcessor(pdf_folder_name=pdf_folder_name, result_folder_name=result_folder_name,
                                 result_json_name=result_json_name)
    pdf_processor.load_existing_results()
    pdf_processor.process_pdfs_txt(save_batch_size=2)

    ### treeBuildWOExapnsion
    results_dict = entityalignment.alignRootNode(result_folder_name, result_json_name, material)

    # 4 construct kg & tree
    tree_name_wo_exp = tree_folder_name + '/' + material + '_wo_exp.pkl'
    if not os.path.exists(tree_name_wo_exp):
        tree_wo_exp = Tree(material.lower(), result_dict=results_dict)
        print('Starting to construct RetroSynthetic Tree...')
        tree_wo_exp.construct_tree()
        treeloader.save_tree(tree_wo_exp, tree_name_wo_exp)
    else:
        tree_wo_exp = treeloader.load_tree(tree_name_wo_exp)
        print('RetroSynthetic Tree wo expansion already loaded.')
    node_count_wo_exp = countNodes(tree_wo_exp)
    all_path_wo_exp = searchPathways(tree_wo_exp)
    print(f'The tree contains {node_count_wo_exp} nodes and {len(all_path_wo_exp)} pathways before expansion.')

    if alignment:
        print('Starting to align the nodes of RetroSynthetic Tree...')

        ### WO Expansion
        tree_name_wo_exp_alg = tree_folder_name + '/' + material + '_wo_exp_alg.pkl'
        if not os.path.exists(tree_name_wo_exp_alg):
            # reactions_wo_exp_alg = entityalignment.entityAlignment(tree_wo_exp.reactions)
            # tree_wo_exp_alg = Tree(material.lower(), reactions=reactions_wo_exp_alg)
            reactions_wo_exp = tree_wo_exp.reactions
            reactions_wo_exp_alg_1 = entityalignment.entityAlignment_1(reactions_dict=reactions_wo_exp)
            reactions_wo_exp_alg_all = entityalignment.entityAlignment_2(reactions_dict=reactions_wo_exp_alg_1)
            tree_wo_exp_alg = Tree(material.lower(), reactions=reactions_wo_exp_alg_all)
            tree_wo_exp_alg.construct_tree()
            treeloader.save_tree(tree_wo_exp_alg, tree_name_wo_exp_alg)
        else:
            tree_wo_exp_alg = treeloader.load_tree(tree_name_wo_exp_alg)
            print('aligned RetroSynthetic Tree wo expansion already loaded.')
        node_count_wo_exp_alg = countNodes(tree_wo_exp_alg)
        all_path_wo_exp_alg = searchPathways(tree_wo_exp_alg)
        print(f'The aligned tree contains {node_count_wo_exp_alg} nodes and {len(all_path_wo_exp_alg)} pathways before expansion.')
        # tree_wo_exp = tree_wo_exp_alg

    ## treeExpansion
    # 5 kg & tree expansion
    results_dict_additional = tree_expansion.treeExpansion(result_folder_name, result_json_name,
                                                           results_dict, material, expansion=expansion, max_iter=5)
    if results_dict_additional:
        results_dict = tree_expansion.update_dict(results_dict, results_dict_additional)
        # results_dict.update(results_dict_additional)

    tree_name_exp = tree_folder_name + '/' + material + '_w_exp.pkl'
    if not os.path.exists(tree_name_exp):
        tree_exp = Tree(material.lower(), result_dict=results_dict)
        print('Starting to construct Expanded RetroSynthetic Tree...')
        tree_exp.construct_tree()
        treeloader.save_tree(tree_exp, tree_name_exp)
    else:
        tree_exp = treeloader.load_tree(tree_name_exp)
        print('RetroSynthetic Tree w expansion already loaded.')

    # nodes & pathway count (tree w exp)
    node_count_exp = countNodes(tree_exp)
    all_path_exp = searchPathways(tree_exp)
    print(f'The tree contains {node_count_exp} nodes and {len(all_path_exp)} pathways after expansion.')

    if alignment:
        ### Expansion
        tree_name_exp_alg = tree_folder_name + '/' + material + '_w_exp_alg.pkl'
        if not os.path.exists(tree_name_exp_alg):
            reactions_exp = tree_exp.reactions
            reactions_exp_alg_1 = entityalignment.entityAlignment_1(reactions_dict=reactions_exp)
            reactions_exp_alg_all = entityalignment.entityAlignment_2(reactions_dict=reactions_exp_alg_1)
            tree_exp_alg = Tree(material.lower(), reactions=reactions_exp_alg_all)
            tree_exp_alg.construct_tree()
            treeloader.save_tree(tree_exp_alg, tree_name_exp_alg)
        else:
            tree_exp_alg = treeloader.load_tree(tree_name_exp_alg)
            print('aligned RetroSynthetic Tree wo expansion already loaded.')
        node_count_exp_alg = countNodes(tree_exp_alg)
        all_path_exp_alg = searchPathways(tree_exp_alg)
        print(f'The aligned tree contains {node_count_exp_alg} nodes and {len(all_path_exp_alg)} pathways after expansion.')
        tree_exp = tree_exp_alg

    all_pathways_w_reactions = reactions_filtration.getFullReactionPathways(tree_exp)

    ## Filtration
    if filtration:
        # filter reactions based on conditions
        reactions_txt_filtered = reactions_filtration.filterReactions(tree_exp)
        # build & save tree
        tree_name_filtered = tree_folder_name + '/' + material + '_filtered' + '.pkl'
        if not os.path.exists(tree_name_filtered):
            print('Starting to construct Filtered RetroSynthetic Tree...')
            tree_filtered = Tree(material.lower(), reactions_txt=reactions_txt_filtered)
            tree_filtered.construct_tree()
            treeloader.save_tree(tree_filtered, tree_name_filtered)
        else:
            tree_filtered = treeloader.load_tree(tree_name_filtered)
            print('Filtered RetroSynthetic Tree already loaded.')
        node_count_filtered = countNodes(tree_filtered)
        all_path_filtered = searchPathways(tree_filtered)
        print(f'The tree contains {node_count_filtered} nodes and {len(all_path_filtered)} pathways after filtration.')

        # filter invalid pathways
        filtered_pathways = reactions_filtration.filterPathways(tree_filtered)
        all_pathways_w_reactions = filtered_pathways

    ### Recommendation
    # recommend based on specific criterion

    # [1]
    prompt_recommend1 = prompts.recommend_prompt_commercial.format(all_pathways = all_pathways_w_reactions)
    recommend1_reactions_txt = recommendReactions(prompt_recommend1, result_folder_name, response_name='recommend_pathway1')

    tree_pathway1 = Tree(material.lower(), reactions_txt=recommend1_reactions_txt)
    print('Starting to construct recommended pathway 1 ...')
    tree_pathway1.construct_tree()
    tree_name_pathway1 = tree_folder_name + '/' + material + '_pathway1' + '.pkl'
    treeloader.save_tree(tree_pathway1, tree_name_pathway1)

if __name__ == '__main__':
    main()
