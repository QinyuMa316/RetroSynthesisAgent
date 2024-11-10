from RetroSynAgent import prompts
from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.GPTAPI import GPTAPI
import json
import random
import re


def filter_pathways(response_filter_pathways, pathways_txt):
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

def filter_reactions(response_filter_reactions, reactions_txt):
    remaining_reactions_txt = response_filter_reactions.split("Remaining Reactions:")[-1]
    result = re.findall(r'Reaction idx: (\d+)', remaining_reactions_txt)
    # remaining_reaction_indices
    id_list = list(map(str, result))
    # Split the string by "Reaction idx:", keeping the parts that are in reaction_ids
    filtered_entries = []
    for entry in reactions_txt.strip().split("\n\n"):
        if any(f"Reaction idx: {rid}" in entry for rid in id_list):
            filtered_entries.append(entry)
    # Join the filtered results into a single string
    filtered_reactions = "\n\n".join(filtered_entries)
    return filtered_reactions

def concat_pathway_and_reactions(reactions_txt, all_path_list):
    # Split the reaction string by lines
    reactions = reactions_txt.strip().split('\n\n')

    # Store the reactions by Reaction idx in a dictionary
    reaction_dict = {}
    for reaction in reactions:
        idx_line = reaction.split('\n')[0]
        idx = idx_line.split(': ')[-1]
        reaction_dict[idx] = reaction

    # Find the entries corresponding to the pathways and output them
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



if __name__ == '__main__':
    material = 'Polyimide'

    # Note: 1. Rebuild the tree according to reactions_tree_filtered

    loader = TreeLoader()
    tree_filtered_name = material + '_filtered2' + '.pkl'
    tree_dir = 'tree_files'
    # tree_dir + '/' +
    # Note:
    tree_filtered = loader.load_tree(tree_dir + '/' +tree_filtered_name)
    img_suffix = '_filtered'
    reactions_tree_filtered = tree_filtered.show_tree(view=False, img_suffix=img_suffix)
    all_path_filtered = tree_filtered.find_all_paths()
    # random.shuffle(all_path_filtered)
    print(f'{len(all_path_filtered)} paths in this tree after filtering')
    # 28

    # [[idx1,idx2], [idx3,idx4,idx5], ...] => idx1, idx2 \n idx3, idx4, idx5 \n
    # all_path_filtered_string = "\n".join([", ".join(map(str, path)) for path in all_path_filtered])

    # Note: 2. Integrating pathways and reactions

    all_pathways = concat_pathway_and_reactions(reactions_tree_filtered, all_path_filtered)
    with open('results_recommendation/all_pathways.txt', 'w') as f:
        f.write(all_pathways)

    # Note: 3. Screening out unreasonable pathways
    with open('results_recommendation/all_pathways.txt', 'r') as f:
        all_pathways = f.read()
    prompt_filter_pathway = prompts.filter_pathway_prompt_template.format(all_pathways=all_pathways)
    response_filtered_pathway = GPTAPI(temperature=0.0).answer_wo_vision(prompt_filter_pathway)
    with open('results_recommendation/filter_pathways_llm_response.txt', 'w') as f:
        f.write(response_filtered_pathway)

    with open('results_recommendation/filter_pathways_llm_response.txt', 'r') as f:
        response_filtered_pathway = f.read()
    filtered_pathways = filter_pathways(response_filtered_pathway, pathways_txt=all_pathways)
    with open('results_recommendation/filtered_pathways.txt', 'w') as f:
        f.write(filtered_pathways)
    """
    28 paths in this tree after filtering
    20 pathways remaining - id_list
    20 pathways remaining - filtered_entries
    """

    # Note: 4. Recommendations are made based on the filtered reaction pathways
    with open('results_recommendation/filtered_pathways.txt', 'r') as f:
        filtered_pathways = f.read()


    prompt_recommend1 = prompts.recommend_prompt_template_condition_v2.format(substance=material, all_pathways=filtered_pathways)
    response1 = GPTAPI(temperature=0.0).answer_wo_vision(prompt_recommend1)
    with open('results_recommendation/recommendation_llm_res_condition.txt', 'w') as f:
        f.write(response1)

    prompt_recommend2 = prompts.recommend_prompt_template_specific_substance.format(substance = material,
                                                                                    all_pathways = filtered_pathways,
                                                                                    initial_reactant = "trifluoromethylbenzene")
    response2 = GPTAPI(temperature=0.0).answer_wo_vision(prompt_recommend2)
    with open('results_recommendation/recommendation_llm_res_specific_sub.txt', 'w') as f:
        f.write(response2)
