import argparse
import os
import re
import json
import copy
from tqdm import tqdm
from RetroSynAgent.pdfProcessor import PDFProcessor
from RetroSynAgent.pdfDownloader import PDFDownloader
from RetroSynAgent.GPTAPI import GPTAPI
from RetroSynAgent import prompts
from RetroSynAgent.treeBuilder import Tree, TreeLoader
from RetroSynAgent.knowledgeGraph import KnowledgeGraph
from RetroSynAgent.entityAlignment import EntityAlignment
from RetroSynAgent.treeExpansion import TreeExpansion

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Process PDFs and extract reactions.")
    parser.add_argument('--material', type=str, required=True, help="Material name for processing.")
    parser.add_argument('--num_results', type=int, required=True, help="Number of PDF to download.")
    parser.add_argument('--filtration', type=str, default="False", choices=["True", "False"], help="Whether to filter reactions.")
    parser.add_argument('--alignment', type=str, default="False", choices=["True", "False"], help="Whether to align entities except for root node.")
    return parser.parse_args()


def countNodes(tree):
    reactions = tree.reactions
    kg = KnowledgeGraph(reactions)
    node_count = kg.G.number_of_nodes()
    return node_count

def searchPathways(tree):
    all_path = tree.find_all_paths()
    return all_path

def filterPathways(response_filter_pathways, pathways_txt):
    remaining_pathway_txt = response_filter_pathways.split("Remaining Reaction Pathways:")[-1]
    # result = re.findall(r'Pathway: (\d+)', remaining_pathway_txt)
    id_list = [line.split("Pathway: ")[1].strip() for line in remaining_pathway_txt.split('\n') if "Pathway: " in line]
    print(f'{len(id_list)} pathways remaining - id_list')
    # remaining_pathway_indices
    # id_list = list(map(str, result))
    filtered_entries = []
    for entry in pathways_txt.strip().split("\n\n"):
        if any(f"Pathway: {id}" in entry for id in id_list):
            filtered_entries.append(entry)
    print(f'{len(filtered_entries)} pathways remaining - filtered_entries')
    filtered_pathways = "\n\n".join(filtered_entries)
    return filtered_pathways

def filterReactions(response_filter_reactions, reactions_txt):
    remaining_reactions_txt = response_filter_reactions.split("Remaining Reactions:")[-1]
    result = re.findall(r'Reaction idx: (\d+)', remaining_reactions_txt)
    # remaining_reaction_indices
    id_list = list(map(str, result))
    # Split the string by "Reaction idx:" and keep only the parts included in reaction_ids
    filtered_entries = []
    for entry in reactions_txt.strip().split("\n\n"):
        if any(f"Reaction idx: {rid}" in entry for rid in id_list):
            filtered_entries.append(entry)
    # Join the filtered results into a single string
    filtered_reactions = "\n\n".join(filtered_entries)
    return filtered_reactions

def concatPathwayandReactions(reactions_txt, all_path_list):
    # Split the reaction string by line
    reactions = reactions_txt.strip().split('\n\n')

    # Store reaction strings in a dictionary indexed by Reaction idx
    reaction_dict = {}
    for reaction in reactions:
        idx_line = reaction.split('\n')[0]
        idx = idx_line.split(': ')[-1]
        reaction_dict[idx] = reaction

    # Find the corresponding entries for each pathway and output them
    output = []
    for path in all_path_list:
        output.append(f"Pathway: {', '.join(path)}\n")
        for idx in path:
            if idx in reaction_dict:
                output.append(reaction_dict[idx] + "\n")
        output.append('\n')

    # Output the result
    result = ''.join(output)
    return result


def main():
    # demo
    # material = 'Polyimide'
    # num_results = 10
    # filtration = False
    # alignment = False

    # # Parse command-line arguments
    args = parse_arguments()
    material = args.material
    num_results = args.num_results
    filtration = args.filtration == "True"  # turn str to bool
    alignment = args.alignment == "True"

    treeloader = TreeLoader()
    entityalignment = EntityAlignment()
    tree_expansion = TreeExpansion()

    pdf_folder_name = 'literature_pdfs_' + material
    result_folder_name = 'results_' + material
    result_json_name = 'llm_results'
    tree_folder_name = 'tree_files'
    os.makedirs(tree_folder_name, exist_ok=True)
    # 1  query literatures & download

    downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name, num_results=num_results, n_thread=3)
    pdf_name_list = downloader.main()

    print(f'successfully downloaded {len(pdf_name_list)} pdfs for {material}')

    # 2 Extract infos from PDF about reactions
    pdf_processor = PDFProcessor(pdf_folder_name=pdf_folder_name, result_folder_name=result_folder_name,
                                 result_json_name=result_json_name)
    pdf_processor.load_existing_results()
    pdf_processor.process_pdfs_txt(save_batch_size=2)
    # 3 entity alignment ( root node)
    results_dict = entityalignment.alignRootNode(result_folder_name, result_json_name, material)

    # 4 construct kg & tree
    tree_wo_exp = Tree(material.lower(), result_dict=results_dict)
    print('Starting to construct RetroSynthetic Tree...')
    tree_wo_exp.construct_tree()
    tree_filename = tree_folder_name + '/' + material + '_wo_exp.pkl'
    treeloader.save_tree(tree_wo_exp, tree_filename)

    if alignment:
        # entity alignment ( other nodes ) wo exp & rebuild the tree after entity alignment
        print('Performing entity alignment...')
        reactions_dict_wo_exp = tree_wo_exp.reactions
        reactions_dict_wo_exp_alg = entityalignment.entityAlignment(reactions_dict_wo_exp)
        print('Rebuilding the tree after entity alignment...')
        tree_wo_exp = Tree(material.lower(), reactions = reactions_dict_wo_exp_alg)
        tree_filename = tree_folder_name + '/' + material + '_wo_exp_alg.pkl'
        treeloader.save_tree(tree_wo_exp, tree_filename)

    # nodes & pathway count (tree wo exp)
    node_count_wo_exp = countNodes(tree_wo_exp)
    all_path_wo_exp = searchPathways(tree_wo_exp)
    print(f'The tree contains {len(all_path_wo_exp)} pathways '
          f'and {node_count_wo_exp} nodes in the knowledge graph before expansion.')

    # 5 kg & tree expansion
    results_dict_additional = tree_expansion.treeExpansion(result_folder_name, result_json_name,
                                                           results_dict, material, expansion = True, max_iter = 5)
    if results_dict_additional:
        results_dict.update(results_dict_additional)
    tree_exp = Tree(material.lower(), result_dict=results_dict)
    print('Starting to construct Expanded RetroSynthetic Tree...')
    tree_exp.construct_tree()
    if tree_exp.unexpandable_substances != set():
        unexp_sub_list = list(tree_exp.unexpandable_substances)
        unexp_sub_string = '\n'.join(unexp_sub_list)
        print(f"\nUnexpandable Substances:\n{unexp_sub_string}\n")
        # with open("unexp_sub_list.json", 'w') as file:
        #     json.dump(unexp_sub_list, file, indent=4)

    tree_filename_exp = tree_folder_name + '/' + material + '_w_exp.pkl'
    treeloader.save_tree(tree_exp, tree_filename_exp)

    if alignment:
        # entity alignment ( other nodes ) w exp & rebuild the tree after entity alignment
        print('Performing entity alignment...')
        reactions_dict_exp = tree_exp.reactions
        reactions_dict_exp_alg = entityalignment.entityAlignment(reactions_dict_exp)
        print('Rebuilding the tree after entity alignment...')
        tree_exp = Tree(material.lower(), reactions=reactions_dict_exp_alg)
        tree_filename_exp = tree_folder_name + '/' + material + '_w_exp_alg.pkl'
        treeloader.save_tree(tree_exp, tree_filename_exp)

    # nodes & pathway count (tree w exp)
    node_count_exp = countNodes(tree_exp)
    all_path_exp = searchPathways(tree_exp)
    print(f'The tree contains {len(all_path_exp)} pathways '
          f'and {node_count_exp} nodes in the knowledge graph after expansion.')
    reactions_tree_exp = tree_exp.get_reactions_in_tree()

    if filtration: # based on condition
        # filter reactions (optional)
        # filter reactions based on conditions
        prompt1 = prompts.filter_reactions_prompt_template.format(reactions=reactions_tree_exp)
        response1 = GPTAPI().answer_wo_vision(prompt1)
        reactions_tree_filtered = filterReactions(response_filter_reactions=response1, reactions_txt=reactions_tree_exp)
        print(f'Filtered approximately {(1 - len(reactions_tree_filtered) / len(reactions_tree_exp)) * 100:.2f}% of reactions.')
        with open(f'{result_folder_name}/reactions_filtered.txt', 'w') as f:
            f.write(reactions_tree_filtered)
        tree_filtered = Tree(material.lower(), reactions_txt=reactions_tree_filtered)
        tree_filtered.construct_tree()
        tree_name_filtered = tree_folder_name + '/' + material + '_filtered' + '.pkl'
        treeloader.save_tree(tree_filtered, tree_name_filtered)
        # nodes & pathway count (tree w filtered)
        node_count_filtered = countNodes(tree_filtered)
        all_path_filtered = searchPathways(tree_filtered)
        print(f'The tree contains {len(all_path_filtered)} pathways '
              f'and {node_count_filtered} nodes in the knowledge graph after filtration.')
        reactions_tree_exp = reactions_tree_filtered
        all_path_exp = all_path_filtered

    # 7 recommend reactions
    # 1) Integrating pathway ids & reactions
    # reactions_tree_exp: str (reaction txt in the tree), all_path_exp: list (reaction pathway idx list)

    all_pathways_w_reactions = concatPathwayandReactions(reactions_tree_exp, all_path_exp)
    if filtration: # unreasonable
        # 2) Screening out unreasonable pathways (optional)
        prompt_filter_pathway = prompts.filter_pathway_prompt_template.format(all_pathways=all_pathways_w_reactions)
        response_filtered_pathway = GPTAPI().answer_wo_vision(prompt_filter_pathway)
        filtered_pathways = filterPathways(response_filtered_pathway, pathways_txt=all_pathways_w_reactions)
        all_pathways_w_reactions = filtered_pathways

    # 3) recommend based on specific criterion
    prompt_recommend1 = prompts.recommend_prompt_template_condition_v2.format(substance=material,
                                                                              all_pathways=all_pathways_w_reactions)
    recommend1 = GPTAPI().answer_wo_vision(prompt_recommend1)
    with open(f'{result_folder_name}/reactions_recommend.txt', 'w') as f:
        f.write(recommend1)

    start_idx = recommend1.find("Recommended Reaction Pathway:")
    recommend1_main = recommend1[start_idx:]
    print(f'\n=================================================='
          f'==========\n{recommend1_main}\n====================='
          f'=======================================\n')
    # The tree contains 6 pathways and 20 nodes in the knowledge graph before expansion.
    # The tree contains 17 pathways and 43 nodes in the knowledge graph after expansion.

    # 8 build recommended pathway as a tree
    tree_pathway1 = Tree(material.lower(), reactions_txt=recommend1_main)
    print('Starting to construct recommended pathway ...')
    tree_pathway1.construct_tree()
    tree_name_pathway1 = tree_folder_name + '/' + material + '_pathway1' + '.pkl'
    treeloader.save_tree(tree_pathway1, tree_name_pathway1)

    # visualize tree (wo_exp, w_exp, recommended_pathway)

if __name__ == '__main__':
    main()


