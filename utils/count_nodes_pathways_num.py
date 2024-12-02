from RetroSynAgent.treebuilder import Tree, TreeLoader
from RetroSynAgent.knowledgegraph import KnowledgeGraph


if __name__ == "__main__":
    material = 'Polyimide'
    loader = TreeLoader()
    tree = loader.load_tree(material+'.pkl')

    # After Expansion


    # NOTE: count the num of nodes in KG
    reactions = tree.reactions
    kg = KnowledgeGraph(reactions)
    # kg.visualize_kg(html_name=f"KG_{material}_expansion.html")
    node_count = kg.G.number_of_nodes()
    print(f'{node_count} nodes in KnowledgeGraph after expansion')

    # NOTE: count the num of pathways in Reaction Tree
    img_suffix = '_40_modified_add'
    reactions_tree = tree.show_tree(view=False, simple=False, img_suffix=img_suffix)
    all_path = tree.find_all_paths()
    print(f'{len(all_path)} pathways in this tree after expansion')  # 830 paths in this tree

    # Before Expansion

    tree2 = loader.load_tree(material + '_wo_exp.pkl')

    # NOTE: count the num of nodes in KG
    reactions2 = tree2.reactions
    kg2 = KnowledgeGraph(reactions2)
    # kg.visualize_kg(html_name=f"KG_{material}.html")
    node_count2 = kg2.G.number_of_nodes()
    print(f'{node_count2} nodes in KnowledgeGraph without expansion')

    # NOTE: count the num of pathways in Reaction Tree
    img_suffix = '_40_modified'
    reactions_tree2 = tree2.show_tree(view=False, simple=False, img_suffix=img_suffix)
    all_path2 = tree2.find_all_paths()
    print(f'{len(all_path2)} pathways in this tree without expansion')
    """
    650 nodes in KnowledgeGraph after expansion
    897 pathways in this tree after expansion
    259 nodes in KnowledgeGraph without expansion
    112 pathways in this tree without expansion
    """

    # todo:
    kg.export_to_json('kg_files/kg_expansion.json')
    kg2.export_to_json('kg_files/kg_origin.json')
