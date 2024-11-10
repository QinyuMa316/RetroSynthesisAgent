from RetroSynAgent import prompts
from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.GPTAPI import GPTAPI
import json
import random
import re


def filter_reactions(response_filter_reactions, reactions_txt):
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

def concat_pathway_and_reactions(reactions_txt, all_path_list):
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



if __name__ == '__main__':

    material = 'Polyimide'
    tree_dir = 'tree_files'
    loader = TreeLoader()
    # Note: 0. Load the original reaction_tree for further filtering
    tree = loader.load_tree(tree_dir + "/" + material + '.pkl')
    # reactions_tree: all reactions (idx, reactants, products, conditions, source) in the tree
    img_suffix = '_40_modified_add'
    reactions_tree = tree.show_tree(view=False, simple=False, img_suffix=img_suffix)

    # Note: 1. Use LLM to filter reactions based on conditions
    prompt1 = prompts.filter_reactions_prompt_template.format(reactions=reactions_tree)
    response1 = GPTAPI(temperature=0.0).answer_wo_vision(prompt1)

    with open('filter_reactions_llm_response.txt', 'w') as f:
        f.write(response1)

    # Note: 2. Filter reactions_tree based on reaction idx provided by LLM
    with open('filter_reactions_llm_response.txt', 'r') as f:
        response1 = f.read()

    reactions_tree_filtered = filter_reactions(response_filter_reactions=response1, reactions_txt=reactions_tree)

    print(f'reactions_tree_filtered: {len(reactions_tree_filtered)}, reactions_tree: {len(reactions_tree)}')
    with open('filtered_reactions.txt', 'w') as f:
        f.write(reactions_tree_filtered)

    # Note: 3. Reconstruct the tree based on reactions_tree_filtered
    with open('filtered_reactions.txt', 'r') as f:
        reactions_tree_filtered = f.read()
    tree_filtered = Tree(material.lower(), reactions_txt=reactions_tree_filtered)
    tree_filtered.construct_tree()
    tree_filtered_name = material + '_filtered' + '.pkl'
    loader.save_tree(tree_filtered, tree_filtered_name)

