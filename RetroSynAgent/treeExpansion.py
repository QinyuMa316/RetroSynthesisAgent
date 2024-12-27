import os
import copy
import json
from . import prompts
from .treeBuilder import Tree, TreeLoader
from .pdfDownloader import PDFDownloader
from .pdfProcessor import PDFProcessor
from .GPTAPI import GPTAPI


class TreeExpansion:
    def update_json_file(self, add_results_filepath, add_results):
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

    def expand_reactions_from_lits(self, result_folder_name, result_json_name, material, origin_result_dict, max_iter = 10):
        add_results_filepath = result_folder_name + '/' + result_json_name + '_modified_add.json'

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
            print(f'Iteration: {iteration}')
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
                        # with open(add_results_filepath, 'r') as f:
                        #     origin_add_results = json.load(f)
                        try:
                            with open(add_results_filepath, 'r') as f:
                                origin_add_results = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError):
                            origin_add_results = {}
                        if pdf_name_wo_suffix not in origin_add_results:
                            pdf_path = pdf_folder_path + '/' + pdf_name
                            pdf_processor = PDFProcessor()
                            # pdf_path = 'substances_name/literature_title.pdf'
                            long_string = pdf_processor.pdf_to_long_string(pdf_path)
                            total_length = len(long_string)
                            print(f'Processing: {pdf_name}, TXT Length: {total_length}')
                            prompt = prompts.prompt_add_reactions_from_lits_template.format(material=substance)
                            llm = GPTAPI()
                            response = llm.answer_wo_vision(prompt, content=long_string)
                            add_results[pdf_name_wo_suffix] = (response,'')
                            # update add results json file
                            self.update_json_file(add_results_filepath, add_results)
                            # {"source": (reactions_txt, properties_txt) }
                            # print('successfully updated added results file.')
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


    def treeExpansion(self, result_folder_name, result_json_name, results_dict, material, expansion = False, max_iter = 10):
        add_results_filepath = result_folder_name + '/' + result_json_name + '_modified_add.json'
        if os.path.exists(add_results_filepath):
            with open(add_results_filepath, 'r') as file:
                add_results = json.load(file)
                results_dict.update(add_results)
            print('Additional reaction data successfully loaded.')
        else:
            add_results = {}
            print('Failed to load additional reaction data. File path does not exist.')

        if expansion:
            print('Starting expansion of the RetroSynthetic tree...')
            # note: key step expand to full
            add_results_new = self.expand_reactions_from_lits(result_folder_name, result_json_name, material,
                                                         origin_result_dict = results_dict,
                                                         max_iter = max_iter)
            if add_results_new:
                add_results.update(add_results_new)
        return add_results
