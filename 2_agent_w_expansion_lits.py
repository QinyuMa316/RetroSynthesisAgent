
import json
from RetroSynAgent.pdfprocessor import PDFProcessor
from RetroSynAgent.reactionparser import ReactionParser
from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.GPTAPI import GPTAPI
from RetroSynAgent.pdfdownloader import PDFDownloader
from RetroSynAgent import prompts
import re
import os
import copy
from RetroSynAgent.knowledgegraph import KnowledgeGraph


def update_json_file(add_results_filepath, add_results):
    # If the file exists, read the file content first
    if os.path.exists(add_results_filepath):
        with open(add_results_filepath, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}  # Initialize as an empty dictionary if the file is empty or corrupted
    else:
        existing_data = {}
    # Update existing data
    existing_data.update(add_results)
    # Write the updated data back to the file
    with open(add_results_filepath, 'w') as f:
        json.dump(existing_data, f, indent=4)


def expand_reactions_from_lits(material, origin_result_dict, add_results_filepath, max_iter = 10):
    os.makedirs('literatures_add', exist_ok=True)
    result_dict = copy.deepcopy(origin_result_dict)
    # additional_reactions_txt = ''
    add_results = {}
    result = False
    unexpandable_substances = set()
    iteration = 1
    # Exit the while loop if result is true and unexpandable_substances is an empty set.
    # Enter the loop if result is false or unexpandable_substances is not an empty set.
    while not result or unexpandable_substances:
        print(f'\n===== iteration: {iteration}\n')
        # 3. build graph & tree
        # tree = Tree(material.lower(), reactions_txt=reactions_text)
        if add_results:
            result_dict.update(add_results)
        tree = Tree(material.lower(), result_dict = result_dict)
        result = tree.construct_tree()
        if tree.unexpandable_substances != set():
            unexp_sub_list = list(tree.unexpandable_substances)
            # unexpandable_substances = '\n'.join(unexp_sub_list)
            # print(f"=== Unexpandable Substances:\n{unexpandable_substances}\n")
            # prompt = prompts.prompt_add_reactions.format(substances=unexpandable_substances)
            for substance in unexp_sub_list:
                pdf_name_list = []
                num_results_tmp = 0
                pdf_folder_path = 'literatures_add/lits_pdf_add_' + substance
                if (not os.path.exists(pdf_folder_path)) or (len(os.listdir(pdf_folder_path)) == 0):
                    while len(pdf_name_list) == 0:
                        num_results_tmp += 5
                        downloader = PDFDownloader(substance, pdf_folder_name=pdf_folder_path,
                                                   num_results=num_results_tmp, n_thread=3)
                        pdf_name_list = downloader.main()
                        if num_results_tmp >= 15:
                            break
                    print(f'successfully downloaded {len(pdf_name_list)} pdfs for {substance}')
                else:
                    # Traverse all files in the folder
                    for file_name in os.listdir(pdf_folder_path):
                        # Check if the file extension is .pdf
                        if file_name.endswith(".pdf"):
                            pdf_name_list.append(file_name)

                for pdf_name in pdf_name_list:
                    pdf_name_wo_suffix = pdf_name.replace('.pdf', '')
                    with open(add_results_filepath, 'r') as f:
                        origin_add_results = json.load(f)
                    if pdf_name_wo_suffix not in origin_add_results:
                        pdf_path = pdf_folder_path + '/' + pdf_name
                        pdf_processor = PDFProcessor()
                        # pdf_path = 'substances_name/literature_title.pdf'
                        long_string = pdf_processor.pdf_to_long_string(pdf_path)
                        prompt = prompts.prompt_add_reactions_from_lits_template.format(material=substance)
                        llm = GPTAPI()
                        response = llm.answer_wo_vision(prompt, content=long_string)
                        add_results[pdf_name_wo_suffix] = (response,'')
                        # update add results json file
                        update_json_file(add_results_filepath, add_results)
                        # {"source": (reactions_txt, properties_txt) }
                        print('successfully updated added results file.')
                    else:
                        print(f'{pdf_name_wo_suffix} has been processsed.')

            iteration += 1
            if iteration == max_iter:
                print('exit loop because exceed max iteration')
                break
        # else: unexpandable_substances == set()
        else:
            # If there are no unexpanded substances, set unexpandable_substances to an empty set
            # This is the key to exiting the loop
            unexpandable_substances = set()

            print('exit loop because set is empty')
    return add_results

if __name__ == '__main__':

    material = 'Polyimide'
    pdf_folder_name = 'literature_pdfs_' + material
    result_folder_name = 'results_' + material
    result_json_name = 'gpt_results_40'
    modified_results_filepath = result_folder_name + '/' + result_json_name + '_modified.json'
    add_results_filepath = result_folder_name + '/' + result_json_name + '_modified_add.json'
    # parser = ReactionParser()
    # reactions, properties_dict, product_dict = parser.process_data(result_folder_name+'/'+result_json_name+'.json')

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



    # note: 2. expand reactions from lits
    if os.path.exists(add_results_filepath):
        with open(add_results_filepath, 'r') as file:
            add_results = json.load(file)
            results_dict.update(add_results)
            print('load added results data')
    else:
        add_results = {}
        print('failed to load added results data, because path does not exist')


    # note: key step expand to full
    # add_results_new = expand_reactions_from_lits(material, results_dict, add_results_filepath, max_iter=3)
    # if add_results_new:
    #     add_results.update(add_results_new)

    # note: 3. build tree
    # update: if the key is the same, it will overwrite the original

    if add_results:
        results_dict.update(add_results) # update in-place operaction return null
        tree = Tree(material.lower(), result_dict=results_dict)
        print('build tree with added reactions')
        img_suffix = '_40_modified_add'
    else:
        tree = Tree(material.lower(), result_dict=results_dict)
        print('build tree without added reactions')
        img_suffix = '_40_modified'


    print('start construct tree...')
    result = tree.construct_tree()
    if tree.unexpandable_substances != set():
        unexp_sub_list = list(tree.unexpandable_substances)
        unexp_sub_string = '\n'.join(unexp_sub_list)
        print(f"\n=== Unexpandable Substances:\n{unexp_sub_string}\n")
        with open("unexp_sub_list.json", 'w') as file:
            json.dump(unexp_sub_list, file, indent=4)

    loader = TreeLoader()
    loader.save_tree(tree, material+'.pkl')



