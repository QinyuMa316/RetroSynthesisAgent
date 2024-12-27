from . import prompts
from .GPTAPI import GPTAPI
import json
import os
from tqdm import tqdm

class EntityAlignment:
    # ensure substance name consistency in different literatures
    def alignRootNode(self, result_folder_name, result_json_name, material):
        modified_results_filepath = result_folder_name + '/' + result_json_name + '_modified.json'
        if not os.path.exists(modified_results_filepath):
            print('Initiating substance name modifications to ensure consistency...')
            with open(result_folder_name + '/' + result_json_name + '.json', 'r') as file:
                results_dict = json.load(file)
                print('Original results data loaded. Beginning modifications...')
            for key, values in tqdm(results_dict.items()):
                reactions_txt = values[0]
                prompt = prompts.prompt_align_root_node.format(substance=material, reactions=reactions_txt)
                # print(f'===== origin txt:\n{reactions_txt}\n')
                llm = GPTAPI()
                reactions_txt_modified = llm.answer_wo_vision(prompt)
                values[0] = reactions_txt_modified
                # print(f'===== modified txt:\n{reactions_txt_modified}\n')

            with open(result_folder_name + '/' + result_json_name + '_modified.json', 'w') as file:
                json.dump(results_dict, file, indent=4)
            print('Substance name modifications completed. Modified data saved.')
        else:
            with open(modified_results_filepath, 'r') as file:
                results_dict = json.load(file)
                print('Modified results data successfully loaded.')
        return results_dict

    def getNamingStdMap(self, reactions_dict):
        all_reactants = set()
        for key, entry in reactions_dict.items():
            reactants = list(entry['reactants'])
            all_reactants.update(reactants)
        all_reactants = list(all_reactants)
        print(f'total num of substances: {len(all_reactants)}')
        #
        llm = GPTAPI(temperature=0.1)
        prompt_naming = prompts.prompt_template_entity_alignment.format(substances=all_reactants)
        align_result = llm.answer_wo_vision(prompt_naming)
        #
        result = {}
        lines = align_result.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Different names for the same substance:"):
                names = line.split("Different names for the same substance:")[1].strip().split(', ')
            elif line.startswith("Standardized name:"):
                std_name = line.split("Standardized name:")[1].strip()
                for name in names:
                    result[name] = std_name
        result = {k.lower(): v.lower() for k, v in result.items()}
        return result

    def entityAlignment(self, reactions_dict):
        naming_std_map = self.getNamingStdMap(reactions_dict)
        for key, entry in reactions_dict.items():
            reactants = list(entry['reactants'])
            for i, reactant in enumerate(reactants):
                if reactant in naming_std_map:
                    reactants[i] = naming_std_map[reactant]
                    if reactant != reactants[i]:
                        print(f"Reactant: {reactant} -> {reactants[i]}")
            entry['reactants'] = tuple(reactants)
            products = list(entry['products'])
            for i, product in enumerate(products):
                if product in naming_std_map:
                    products[i] = naming_std_map[product]
                    if product != products[i]:
                        print(f"Product: {product} -> {products[i]}")
            entry['products'] = tuple(products)
        return reactions_dict


