from . import prompts
from .GPTAPI import GPTAPI
import json
import os
from tqdm import tqdm
import re
import time

class EntityAlignment:
    # ensure substance name consistency in different literatures
    def alignRootNode(self, result_folder_name, result_json_name, material):
        # modified_results_filepath = result_folder_name + '/' + result_json_name + '_modified.json'
        # original_results_filepath = result_folder_name + '/' + result_json_name + '.json'
        modified_results_filepath = os.path.join(result_folder_name, result_json_name + '_modified.json')
        original_results_filepath = os.path.join(result_folder_name, result_json_name + '.json')

        with open(original_results_filepath, 'r') as file:
            results_dict = json.load(file)
            # print('Original results data loaded.')
        if not os.path.exists(modified_results_filepath):
            print('Starting entity alignment to ensure consistency in substance names...')
            results_dict_modified = results_dict.copy()
            for key, reactions_txt in tqdm(results_dict_modified.items()):
                prompt = prompts.prompt_align_root_node.format(substance=material, reactions=reactions_txt)
                llm = GPTAPI()
                reactions_txt_modified = llm.answer_wo_vision(prompt).replace("′","'")
                results_dict_modified[key] = reactions_txt_modified
                # print(f'\n=== origin txt:{reactions_txt}\n=== modified txt:\n{reactions_txt_modified}')
        else:
            with open(modified_results_filepath, 'r') as file:
                results_dict_modified = json.load(file)
                print('Modified results data successfully loaded.')
                if len(results_dict_modified) == len(results_dict):
                    return results_dict_modified
                else:
                    print('Starting entity alignment to ensure consistency in substance names...')
                    for key, reactions_txt in tqdm(results_dict.items()):
                        if not key in results_dict_modified:
                            prompt = prompts.prompt_align_root_node.format(substance=material, reactions=reactions_txt)
                            llm = GPTAPI()
                            reactions_txt_modified = llm.answer_wo_vision(prompt).replace("′", "'")
                            results_dict_modified[key] = reactions_txt_modified
                            # print(f'\n=== origin txt:{reactions_txt}\n=== modified txt:\n{reactions_txt_modified}')
                        # else:
        with open(result_folder_name + '/' + result_json_name + '_modified.json', 'w') as file:
            json.dump(results_dict_modified, file, indent=4, ensure_ascii=False)
        print('Substance name modifications completed. Modified data saved.')


        return results_dict_modified

    def getNamingStdMap_2(self, reactions_dict):
        # th
        # smiles_pattern = re.compile(r'^[A-Za-z0-9@+\-#\(\)\\/\=\[\]\.\%\:\?]*$')
        all_substances = set()
        for key, entry in reactions_dict.items():
            reactants = list(entry['reactants'])
            # all_reactants.update(reactants)
            for reactant in reactants:
                # if not smiles_pattern.match(reactant):
                    all_substances.add(reactant)
            products = list(entry['products'])
            for product in products:
                # if not smiles_pattern.match(product):
                    all_substances.add(product)
        all_substances = list(all_substances)
        # print(f'total num of Mols: {len(all_substances)}')
        #
        llm = GPTAPI(temperature=0.0)
        prompt_naming = prompts.prompt_template_entity_alignment.format(substances=all_substances)
        align_result = llm.answer_wo_vision(prompt_naming)
        #
        filename = "naming_alg_llm_res.json"
        if not os.path.exists(filename):
            print(f'fail to load {filename}')
            # result = {}
            llm_res = {}
            lines = align_result.strip().splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("Different names for the same substance:"):
                    names = line.split("Different names for the same substance:")[1].strip().split(', ')
                elif line.startswith("Standardized name:"):
                    std_name = line.split("Standardized name:")[1].strip()
                    llm_res[std_name] = names
                    # for name in names:
                    #     result[name] = std_name
            # we highly recommend to check it because of hallucinations fo LLMs
            with open(filename, 'w') as file:
                json.dump(llm_res, file, indent=4, ensure_ascii=False)
        else:
            with open(filename, 'r') as file:
                llm_res = json.load(file)
            print(f'suceessfully loaded {filename}')
            result = {}
            for std_name, names in llm_res.items():
                for name in names:
                    result[std_name] = name

        result = {k.lower(): v.lower() for k, v in result.items()}
        naming_std_map_2 = {}
        for key, value in result.items():
            if key != value:
                naming_std_map_2[key] = value
        # key: sub 1, value: sub 2
        # sub 1 -> sub 2
        return naming_std_map_2


    def getNamingStdMap_1(self):
        with open('smiles_cache.json', 'r') as file:
            data = json.load(file)
        name2smiles = {}
        for key, value in data.items():
            if key != value:
                name2smiles[key] = value
        # name2smiles example
        # "pyromellitic dianhydride": "C1=C2C(=CC3=C1C(=O)OC3=O)C(=O)OC2=O",
        smiles2names = {}
        for name, smiles in name2smiles.items():
            if smiles not in smiles2names:
                smiles2names[smiles] = []
            smiles2names[smiles].append(name)
        # smiles2name example
        #     "C1=C2C(=CC3=C1C(=O)OC3=O)C(=O)OC2=O": [
        #         "pyromellitic dianhydride",
        #         "1,2,4,5-benzenetetracarboxylic dianhydride"
        #     ],
        hashmap = {}
        for smiles, name_list in smiles2names.items():
            if len(name_list) > 1:
                hashmap[name_list[0]] = name_list
        # hashmap example
        #     "pyromellitic dianhydride": [
        #         "pyromellitic dianhydride",
        #         "1,2,4,5-benzenetetracarboxylic dianhydride"
        #     ],
        naming_std_map = {}
        for key, value_list in hashmap.items():
            for value in value_list:
                if value != key:
                    naming_std_map[value] = key
        #     "1,2,4,5-benzenetetracarboxylic dianhydride": "pyromellitic dianhydride",
        # sub 1 -> sub 2
        return naming_std_map

    def entityAlignment_1(self, reactions_dict):

        # mols that successfully be converted to smiles
        filename = 'synonym_hashmap_1.json'
        if os.path.exists(filename):
            with open('synonym_hashmap_1.json', 'r') as file:
                naming_std_map = json.load(file)
            print(f'successfully loaded{filename}')
        else:
            print(f'fail to load {filename}')
            naming_std_map = self.getNamingStdMap_1()
            with open('synonym_hashmap_1.json', 'w') as file:
                json.dump(naming_std_map, file, indent=4, ensure_ascii=False)

        for key, entry in reactions_dict.items():
            reactants = list(entry['reactants'])
            for i, reactant in enumerate(reactants):
                if reactant in naming_std_map:
                    reactants[i] = naming_std_map[reactant]
                    print(f"Reactant: {reactant} -> {reactants[i]}")
            entry['reactants'] = tuple(reactants)

            products = list(entry['products'])
            for i, product in enumerate(products):
                if product in naming_std_map:
                    products[i] = naming_std_map[product]
                    print(f"Product: {product} -> {products[i]}")
            entry['products'] = tuple(products)
        return reactions_dict

    def entityAlignment_2(self, reactions_dict):
        # mols that fail to be converted to smiles
        filename = 'synonym_hashmap_2.json'
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                naming_std_map_2 = json.load(file)
            print(f'successfully loaded {filename}')
        else:
            print(f'fail to load {filename}')
            naming_std_map_2 = self.getNamingStdMap_2(reactions_dict)
            with open(filename, 'w') as file:
                json.dump(naming_std_map_2, file, indent=4, ensure_ascii=False)

        for key, entry in reactions_dict.items():
            reactants = list(entry['reactants'])
            for i, reactant in enumerate(reactants):
                if reactant in naming_std_map_2:
                    reactants[i] = naming_std_map_2[reactant]
                    print(f"Reactant: {reactant} -> {reactants[i]}")
            entry['reactants'] = tuple(reactants)

            products = list(entry['products'])
            for i, product in enumerate(products):
                if product in naming_std_map_2:
                    products[i] = naming_std_map_2[product]
                    print(f"Product: {product} -> {products[i]}")
            entry['products'] = tuple(products)

        return reactions_dict
