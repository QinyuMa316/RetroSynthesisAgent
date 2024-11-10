import os
import json
import fitz  # PyMuPDF
import re
from tqdm import tqdm
import difflib
import glob
from . import prompts
from .GPTAPI import GPTAPI
import base64
from io import BytesIO
from PIL import Image


class PDFProcessor:
    def __init__(self, pdf_folder_name=None, result_folder_name = os.getcwd(), result_json_name='gpt_results'):
        self.pdf_folder_name = pdf_folder_name
        self.result_folder_name = result_folder_name
        self.result_json_name = result_json_name
        self.result_dict = {}
        self.processed_pdf_list = []

    def load_existing_results(self):
        if os.path.exists(self.result_folder_name + '/'  + self.result_json_name + '.json'):
            self.result_dict = self.read_data_from_json(self.result_folder_name + '/' + self.result_json_name + '.json')
            self.processed_pdf_list = list(self.result_dict.keys())
            print('Successfully Loaded existing results')
        else:
            print(f"Result JSON does not exist")

    @staticmethod
    def get_pdf_files(directory):
        pdf_files = glob.glob(os.path.join(directory, '*.pdf'))
        return [os.path.basename(file) for file in pdf_files]

    @staticmethod
    def check_pdf_existence(target_pdf_name, pdf_name_list, similarity_threshold=0.9):
        for pdf_name in pdf_name_list:
            similarity = difflib.SequenceMatcher(None, target_pdf_name, pdf_name).ratio()
            if similarity > similarity_threshold:
                return True
        return False

    @staticmethod
    def read_data_from_json(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod
    def save_data_as_json(filename, data):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def pdf_to_base64_img_list(self, pdf_path, zoom_x=3.0, zoom_y=3.0):
        """
        Convert each page of the PDF file to a single image and output it as a Base64 encoded string.
        """
        doc = fitz.open(pdf_path)
        base64_images = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            matrix = fitz.Matrix(zoom_x, zoom_y)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Convert the image to a Base64 string
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            base64_images.append(img_base64)

        doc.close()

        return base64_images

    def remove_references_section(self, text, keyword="REFERENCES"):
        # Find the position of the keyword
        # Convert both the keyword and cleaned_text to uppercase, then find the position of the keyword (this ensures case-insensitive matching)
        keyword_pos = text.upper().rfind(keyword)
        # rfind starts searching from the right, meaning if the keyword appears multiple times, the last occurrence is used
        # keyword_lower = keyword.lower()
        # keyword_pos = self.cleaned_text.lower().find(keyword_lower)
        # If the keyword is found, truncate the string
        if keyword_pos != -1:
            text_filtered_reference = text[:keyword_pos].strip()
        else:
            text_filtered_reference = text
        return text_filtered_reference

    def pdf_to_long_string(self, pdf_path, remove_references=True):
        document = fitz.open(pdf_path)
        raw_text = ''
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            raw_text += page.get_text()
        document.close()
        text = raw_text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s,.]', '', text)
        cleaned_text = text.strip()
        if remove_references:
            cleaned_text = self.remove_references_section(cleaned_text)
        return cleaned_text


    def process_pdfs_img_txt(self, save_batch_size=3, material=None):

        pdf_file_list = self.get_pdf_files(self.pdf_folder_name)
        pdf_name_list = [pdf.split('.pdf')[0] for pdf in pdf_file_list]

        pdf_name_to_process = [
            title for title in pdf_name_list
            if not self.check_pdf_existence(title, self.processed_pdf_list)
        ]
        pdf_file_to_process = [pdf_name + '.pdf' for pdf_name in pdf_name_to_process]

        print(f'Total number of titles: {len(pdf_name_list)}, '
              f'{len(self.processed_pdf_list)} have been processed by MLLM, '
              f'{len(pdf_name_to_process)} are planned to be processed by MLLM')

        os.makedirs(self.result_folder_name, exist_ok=True)
        counter = 0
        for pdf_path in tqdm(pdf_file_to_process):
            pdf_name = pdf_path.replace('.pdf', '')
            base64_img_list = self.pdf_to_base64_img_list(os.path.join(self.pdf_folder_name, pdf_path))
            cleaned_text = self.pdf_to_long_string(os.path.join(self.pdf_folder_name, pdf_path), remove_references=True)
            total_length = len(base64_img_list)+len(cleaned_text)
            print(f'Processing: {pdf_name}, TXT Length: {len(cleaned_text)}, IMG Num: {len(base64_img_list)}')
            # todo: max length
            if total_length > 200000:
                print(f'{pdf_name} Exceed maximum length, skip ...')
                continue
            # Extract the reaction first, then extract the property based on the reaction
            # extract reaction
            llm = GPTAPI()
            prompt = prompts.reaction_prompt
            answer_reaction = llm.answer_w_vision_img_list_txt(prompt, base64_img_list, cleaned_text)
            # answer_reaction = llm.answer_wo_vision(prompt, cleaned_text)
            # extract property
            # prompt2 = prompts.property_prompt.format(reactions=answer_reaction)
            # answer_property = llm.answer_w_vision_img_list_txt(prompt2, base64_img_list, cleaned_text)
            # todo:
            answer_property = ''
            self.result_dict[pdf_name] = (answer_reaction, answer_property)
            counter += 1

            if counter % save_batch_size == 0:
                self.save_data_as_json(f"{self.result_folder_name}/{self.result_json_name}.json", self.result_dict)
                print(f"Saved result after processing {counter} files.")

        self.save_data_as_json(f"{self.result_folder_name}/{self.result_json_name}.json", self.result_dict)
        print(f"Saved result after processing all files.")
        # return self.result_dict
        reactions_txt = ''
        for key, value in self.result_dict.items():
            reactions = value[0]
            reactions_txt += reactions
        return reactions_txt


    def process_pdfs_txt(self, save_batch_size=3, material=None):

        pdf_file_list = self.get_pdf_files(self.pdf_folder_name)
        pdf_name_list = [pdf.split('.pdf')[0] for pdf in pdf_file_list]

        pdf_name_to_process = [
            title for title in pdf_name_list
            if not self.check_pdf_existence(title, self.processed_pdf_list)
        ]
        pdf_file_to_process = [pdf_name + '.pdf' for pdf_name in pdf_name_to_process]

        print(f'Total number of titles: {len(pdf_name_list)}, '
              f'{len(self.processed_pdf_list)} have been processed by MLLM, '
              f'{len(pdf_name_to_process)} are planned to be processed by MLLM')

        os.makedirs(self.result_folder_name, exist_ok=True)
        counter = 0
        for pdf_path in tqdm(pdf_file_to_process):
            pdf_name = pdf_path.replace('.pdf', '')
            # base64_img_list = self.pdf_to_base64_img_list(os.path.join(self.pdf_folder_name, pdf_path))
            cleaned_text = self.pdf_to_long_string(os.path.join(self.pdf_folder_name, pdf_path))
            total_length = len(cleaned_text)
            print(f'Processing: {pdf_name}, TXT Length: {total_length}')
            if total_length > 200000: # 93710
                print(f'{pdf_name} Exceed maximum length, skip ...')
                continue
            llm = GPTAPI()
            prompt = prompts.reaction_prompt
            answer_reaction = llm.answer_wo_vision(prompt, cleaned_text)
            # prompt2 = prompts.property_prompt.format(reactions=answer_reaction)
            # answer_property = llm.answer_wo_vision(prompt2, cleaned_text)
            answer_property = ''
            self.result_dict[pdf_name] = (answer_reaction, answer_property)
            counter += 1
            if counter % save_batch_size == 0:
                self.save_data_as_json(f"{self.result_folder_name}/{self.result_json_name}.json", self.result_dict)
                print(f"Saved result after processing {counter} files.")

        # if counter % save_batch_size != 0:
        #     self.save_data_as_json(f"{self.result_folder_name}/{self.result_json_name}.json", self.result_dict)
        #     print(f"Saved result after processing all files.")
        self.save_data_as_json(f"{self.result_folder_name}/{self.result_json_name}.json", self.result_dict)
        print(f"Saved result after processing all files.")
        # return self.result_dict
        reactions_txt = ''
        for key, value in self.result_dict.items():
            reactions = value[0]
            reactions_txt += (reactions + '\n\n')
        return reactions_txt

