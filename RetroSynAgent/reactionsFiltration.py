import re
import os
from .treeBuilder import Tree, TreeLoader
from . import prompts
from .GPTAPI import GPTAPI

class ReactionsFiltration:
    def __init__(self, result_folder_name = 'res_pi'):
        self.result_folder_name = result_folder_name

    def filterReactions(self, tree):
        reactions_txt = tree.get_reactions_in_tree()
        #
        # with open(f'{self.result_folder_name}/reactions_in_tree.txt', 'w') as f:
        #     f.write(reactions_txt)
        #
        # 1) filter reactions based on conditions
        filename = f'{self.result_folder_name}/reactions_filtered.txt'
        if not os.path.exists(filename):
            prompt_filter_reactions = prompts.prompt_reactions_filtration.format(reactions=reactions_txt)
            response_filter_reactions = GPTAPI(temperature=0.3).answer_wo_vision(prompt_filter_reactions)
            with open(f'{self.result_folder_name}/reactions_filtered.txt', 'w') as f:
                f.write(response_filter_reactions)
        else:
            with open(f'{self.result_folder_name}/reactions_filtered.txt', 'r') as f:
                response_filter_reactions = f.read()

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
        reactions_txt_filtered = "\n\n".join(filtered_entries)
        print(f'Filtered approximately {(1 - len(reactions_txt_filtered) / len(reactions_txt)) * 100:.2f}% of reactions.')
        return reactions_txt_filtered

    def __concatPathwayandReactions(self, reactions_txt, all_path_list):
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

    def getFullReactionPathways(self, tree):
        all_path = tree.find_all_paths()
        reactions_tree = tree.get_reactions_in_tree()
        res = self.__concatPathwayandReactions(reactions_txt=reactions_tree, all_path_list=all_path)
        return res


    def __filter_pathways(self, response_filter_pathways, pathways_txt):
        remaining_pathway_txt = response_filter_pathways.split("Remaining Reaction Pathways:")[-1]
        # result = re.findall(r'Pathway: (\d+)', remaining_pathway_txt)
        id_list = [line.split("Pathway: ")[1].strip() for line in remaining_pathway_txt.split('\n') if
                   "Pathway: " in line]
        # remaining_pathway_indices
        # id_list = list(map(str, result))
        filtered_entries = []
        for entry in pathways_txt.strip().split("\n\n"):
            if any(f"Pathway: {id}" in entry for id in id_list):
                filtered_entries.append(entry)
        # print(f'{len(id_list)} pathways remaining - id_list')
        # print(f'{len(filtered_entries)} pathways remaining - filtered_entries')
        print(f'{len(filtered_entries)} pathways remaining')
        filtered_pathways = "\n\n".join(filtered_entries)
        return filtered_pathways

    def filterPathways(self, tree):
        all_pathways_w_reactions = self.getFullReactionPathways(tree)
        # with open(f'{self.result_folder_name}/all_pathways.txt', 'w') as f:
        #     f.write(all_pathways_w_reactions)

        filename = f'{self.result_folder_name}/pathway_filtered.txt'
        if not os.path.exists(filename):
            prompt_filter_pathway = prompts.prompt_filter_pathway.format(all_pathways=all_pathways_w_reactions)
            response_filtered_pathway = GPTAPI(temperature=0.2).answer_wo_vision(prompt_filter_pathway)
            with open(f'{self.result_folder_name}/pathway_filtered.txt', 'w') as f:
                f.write(response_filtered_pathway)
        else:
            with open(f'{self.result_folder_name}/pathway_filtered.txt', 'r') as f:
                response_filtered_pathway = f.read()
        filtered_pathways = self.__filter_pathways(response_filtered_pathway, pathways_txt=all_pathways_w_reactions)
        return filtered_pathways

