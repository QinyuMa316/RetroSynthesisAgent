from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
from RetroSynAgent.treeBuilder import TreeLoader, Tree
import os
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# define node in js
class Node(BaseModel):
    name: str
    children: Optional[List['Node']] = None
    is_leaf: Optional[bool] = None

# Node.update_forward_refs() is deprecated

# example tree structure for js - v1
# def create_tree():
#     return Node(name="Root", children=[
#         Node(name="Child 1", children=[
#             Node(name="Child 1.1"),
#             Node(name="Child 1.2"),
#         ]),
#         Node(name="Child 2", children=[
#             Node(name="Child 2.1"),
#             Node(name="Child 2.2", children=[
#                 Node(name="Child 2.2.1")
#             ])
#         ])
#     ])



# De-duplicate child nodes - v1
def convert_tree_to_fastapi_node(node):
    # Recursion termination condition, if there are no child nodes
    if not node.children:
        return Node(name=node.substance)

    # Used to store processed subnode names to prevent duplication
    unique_children = []
    seen_substances = set()

    # Traverse the child nodes, remove duplicates and recursively construct
    for child in node.children:
        if child.substance not in seen_substances:
            unique_children.append(convert_tree_to_fastapi_node(child))
            seen_substances.add(child.substance)

    # Construct the current node and return
    return Node(name=node.substance, children=unique_children)


# No deduplication mechanism is used
# def convert_tree_to_fastapi_node(node):
#     if not node.children:
#         return Node(name=node.substance)
#
#     unique_children = []
#     for child in node.children:
#         unique_children.append(convert_tree_to_fastapi_node(child))
#
#     return Node(name=node.substance, children=unique_children)



# Modify the create_tree function to use the converted tree
def create_tree_from_saved_tree(tree):
    return convert_tree_to_fastapi_node(tree.root)


# example tree structure for js - v2
# def create_tree2():
#     return Node(name="Root", is_leaf=False, children=[
#         Node(name="Child 1", children=[
#             Node(name="Child 1.1", is_leaf=False),
#             Node(name="Child 1.2", is_leaf=False),
#         ]),
#         Node(name="Child 2", children=[
#             Node(name="Child 2.1", is_leaf=False),
#             Node(name="Child 2.2", is_leaf=False ,children=[
#                 Node(name="Child 2.2.1", is_leaf=True)
#             ])
#         ])
#     ])

# De-duplicate child nodes - v2
def convert_tree_to_fastapi_node_2(node):
    # Recursion termination condition, if there are no child nodes
    if not node.children:
        # print(f"Leaf node: {node.substance}, is_leaf={node.is_leaf}")
        return Node(name=node.substance, is_leaf=node.is_leaf)

    # Used to store processed subnode names to prevent duplication
    unique_children = []
    seen_substances = set()

    # Traverse the child nodes, remove duplicates and recursively construct
    for child in node.children:
        if child.substance not in seen_substances:
            unique_children.append(convert_tree_to_fastapi_node_2(child))
            seen_substances.add(child.substance)

    # Construct the current node and return
    return Node(name=node.substance, is_leaf = node.is_leaf, children=unique_children)

def create_tree_from_saved_tree_2(tree):
    return convert_tree_to_fastapi_node_2(tree.root)

def count_nodes(node: Node) -> int:
    count = 1
    if node.children:
        for child in node.children:
            count += count_nodes(child)
    return count


material = 'Polyimide'

tree_loader = TreeLoader()

# tree_folder = 'tree_pi/0108-alg2-final'
tree_folder = 'tree_pi'
# main_tree
tree_main_filename = f'{tree_folder}/{material}_w_exp_alg.pkl'
# sub_tree_1_purple
# tree_filtered_filename = f"{tree_folder}/{material}_filtered.pkl"
# sub_tree_2_black
tree_wo_exp_filename = f'{tree_folder}/{material}_wo_exp_alg.pkl'
# pathway1
path_1 = f"{tree_folder}/{material}_pathway1.pkl"
# pathway2
path_2 = f"{tree_folder}/{material}_pathway2.pkl"


if os.path.exists(tree_main_filename):
    tree_main = tree_loader.load_tree(tree_main_filename)
    tree_main_api = create_tree_from_saved_tree_2(tree_main)
    print(f'successfully loaded tree after expansion, '
          f'{tree_main.get_node_count()} nodes in original tree, '
          f'{count_nodes(tree_main_api)} nodes in api tree.')
# if os.path.exists(tree_filtered_filename):
#     tree_filtered = tree_loader.load_tree(tree_filtered_filename)
#     tree_filtered_api = create_tree_from_saved_tree_2(tree_filtered)
if os.path.exists(tree_wo_exp_filename):
    tree_wo_exp = tree_loader.load_tree(tree_wo_exp_filename)
    tree_wo_exp_api = create_tree_from_saved_tree_2(tree_wo_exp)
    print(f'successfully loaded tree before expansion, '
          f'{tree_wo_exp.get_node_count()} nodes in original tree, '
          f'{count_nodes(tree_wo_exp_api)} nodes in api tree.')
if os.path.exists(path_1):
    path1_tree = tree_loader.load_tree(path_1)
    path1_tree_api = create_tree_from_saved_tree_2(path1_tree)
if os.path.exists(path_2):
    path2_tree = tree_loader.load_tree(path_2)
    path2_tree_api = create_tree_from_saved_tree_2(path2_tree)


# tree_test_filename = f'{tree_folder}/{material}_w_exp_alg_0.pkl'
#
# if os.path.exists(tree_test_filename):
#     tree_test = tree_loader.load_tree(tree_test_filename)
#     tree_test_api = create_tree_from_saved_tree_2(tree_test)


# main page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 1 tree
# @app.get("/api/tree", response_model=Node)
# async def get_tree():
#     # return create_tree()
#     # return api_tree
#     return tree_test_api

# 2 trees
@app.get("/api/double")
async def get_double():
    print("TWO")

    return {
        "bigTree": tree_main_api,
        "smallTree": tree_wo_exp_api
    }


# 3 trees
@app.get("/api/three")
async def get_three():
    print("THREE")
    return {
        "main": tree_main_api,
        "son": tree_wo_exp_api,
        "path1": path1_tree_api,
    }

# 4 trees
@app.get("/api/quad")
async def get_quadruple():
    print("FOUR")
    return {
        "main": tree_main_api,
        "son": tree_wo_exp_api,
        "path1": path1_tree_api,
        "path2": path2_tree_api
    }

# 5 trees
# @app.get("/api/five")
# async def get_five():
#     print("FIVE")
#     return {
#         "main": tree_main_api,
#         "son": tree_filtered_api,
#         "path1": path1_tree_api,
#         "path2": path2_tree_api,
#         "black_tree": tree_wo_exp_api
#     }

