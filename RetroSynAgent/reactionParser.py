'''
reactants = [reactant1, reactant2, ...]
products = [product1, product2, ...]
reactions = [[[reactant1, reactant2, ...], [product1, product2, ...]], ....]
product_dict = {'s1':[idx1,idx2,...],'s2':[...]} # s1 is obtained by raction-idx1 or idx2
'''
import json
import networkx as nx
from pyvis.network import Network

import warnings
warnings.filterwarnings('ignore')

class ReactionParser:
    @staticmethod
    def read_data_from_json(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    @staticmethod
    def save_data_as_json(filename, data):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def get_product_dict(self, reactions_dict):
        '''
        reactions_dict[str(idx)] = {
            'reactants': tuple(reactants),
            'products': tuple(products),
            'conditions': conditions,
        }
        '''
        product_dict = {}
        # Iterate over the reactions_entry dictionary
        for idx, entry in reactions_dict.items():
            products = entry['products']
            # Iterate over products
            for product in products:
                product = product.strip()
                if product not in product_dict:
                    product_dict[product] = []
                product_dict[product].append(idx)

        for key, value in product_dict.items():
            product_dict[key] = tuple(value)
        return product_dict

    def parse_reactions(self, reactions_txt):
        idx = 1
        reactants = []
        products = []
        reactions_dict = {}
        lines = reactions_txt.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Reactants:"):
                reactants = line.split("Reactants:")[1].strip().split(', ')
                reactants = [reactant.lower() for reactant in reactants]
            elif line.startswith("Products:"):
                products = line.split("Products:")[1].strip().split(', ')
                products = [product.lower() for product in products]
            elif line.startswith("Conditions:"):
                conditions = line.split("Conditions:")[1].strip()
                reactions_dict[str(idx)] = {
                    'reactants': tuple(reactants),
                    'products': tuple(products),
                    'conditions': conditions,
                }
                idx += 1
        return reactions_dict

    def parse_properties(self, properties_txt):
        properties_dict = {}
        material_name = None
        lines = properties_txt.splitlines()  # Split text into lines

        for line in lines:
            line = line.strip()  # Remove spaces from each line
            if line.startswith("Material"):  # Check for the start of a new material
                if material_name:  # If a material has already been parsed, store it in the dictionary
                    properties_dict[material_name] = properties_entry
                properties_entry = {}  # Initialize the dictionary for the new material
            elif line.startswith("Substance:"):
                material_name = line.split("Substance:")[1].strip().lower()
            elif line.startswith("Name:"):
                material_name = line.split("Name:")[1].strip().lower()
            elif line.startswith("Number Average Molecular Weight:"):
                properties_entry["num_avg_mol_weight"] = line.split("Number Average Molecular Weight:")[1].strip()
            elif line.startswith("Weight Average Molecular Weight:"):
                properties_entry["weight_avg_mol_weight"] = line.split("Weight Average Molecular Weight:")[1].strip()
            elif line.startswith("Polydispersity Index (PDI):"):
                properties_entry["PDI"] = line.split("Polydispersity Index (PDI):")[1].strip()
            elif line.startswith("Decomposition temperature:"):
                properties_entry["Td"] = line.split("Decomposition temperature:")[1].strip()
            elif line.startswith("Glass transition temperature:"):
                properties_entry["Tg"] = line.split("Glass transition temperature:")[1].strip()
            # elif line.startswith("Mechanical properties:"):
            #     properties_entry["mechanical"] = line.split("Mechanical properties:")[1].strip()
            # elif line.startswith("Other properties:"):
            #     properties_entry["other"] = line.split("Other properties:")[1].strip()

        # Add the last material to the dictionary (if any)
        if material_name:
            properties_dict[material_name] = properties_entry

        return properties_dict

    def process_data(self, input_filename,
                     output_reactions_filename=None,
                     output_properties_filename=None):#,output_product_dict_filename=None):
        data = self.read_data_from_json(input_filename)

        # for pdf_name, reactions_text in data.items():
        #     self.parse_reactions(reactions_text, pdf_name)
        # product_dict = self.get_product_dict()

        reactions_text = ''
        properties_text = ''
        for reaction, property in data.values():
            reactions_text += reaction + '\n\n'
            properties_text += property + '\n\n'

        # todo: just for test
        # print(f"===== reactions_text: \n\n{reactions_text}")

        lines = properties_text.splitlines()
        lines = [line for line in lines if all(phrase not in line for phrase in ["Not specified", "Not specifically mentioned", "unspecified", "Unspecified"])]
        properties_text = "\n".join(lines)
        # print(f"===== properties_text: \n\n{properties_text}")

        # with open('results15/origin_reactions.txt', 'w') as file:
        #     file.write(reactions_text)
        # with open('results15/origin_properties.txt', 'w') as file:
        #     file.write(properties_text)

        reactions_dict = self.parse_reactions(reactions_text)
        # self.get_product_dict()
        properties_dict = self.parse_properties(properties_text)
        # product_dict = self.get_product_dict(reactions_dict)
        # save files (optional)
        if output_reactions_filename:
            self.save_data_as_json(output_reactions_filename, reactions_dict)
        if output_properties_filename:
            self.save_data_as_json(output_properties_filename, properties_dict)
        # if output_product_dict_filename:
        #     self.save_data_as_json(output_product_dict_filename, product_dict)
        return reactions_dict, properties_dict #, product_dict


