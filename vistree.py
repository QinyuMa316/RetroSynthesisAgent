from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
from RetroSynAgent.treeBuilder import TreeLoader, Tree

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 节点定义
class Node(BaseModel):
    name: str
    children: Optional[List['Node']] = None

# Node.update_forward_refs() is deprecated

# example tree structure for js
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


def convert_tree_to_fastapi_node(node):
    # v2 对孩子节点进行去重
    # 递归终止条件，如果没有子节点
    if not node.children:
        return Node(name=node.substance)

    # 用于存储已处理的子节点名称，防止重复
    unique_children = []
    seen_substances = set()

    # 遍历子节点，去重并递归构造
    for child in node.children:
        if child.substance not in seen_substances:
            unique_children.append(convert_tree_to_fastapi_node(child))
            seen_substances.add(child.substance)

    # 构造当前节点并返回
    return Node(name=node.substance, children=unique_children)

# 修改create_tree函数以使用转换后的树
def create_tree_from_saved_tree(tree):
    return convert_tree_to_fastapi_node(tree.root)

material = 'Polyimide'

# 【测试用例1】
# from RetroSynAgent.treebuilder2 import TreeLoader, Tree
# with open('reactions_test.txt', 'r') as file:
#     reactions_txt = file.read()
# target_substance = 'X'
# tree = Tree(target_substance.lower(), reactions_txt=reactions_txt)
# tree.construct_tree()


tree_loader = TreeLoader()

# 【主图】
tree_main_filename = f'tree_files/{material}_w_exp.pkl'
# 【子图】- 玫红色
# tree_filtered_filename = f'tree_files/{material}_filtered.pkl'
# 【子图2】- 黑色
tree_wo_exp_filename = f'tree_files/{material}_wo_exp.pkl'
# 【路径1】
path_1 = f"tree_files/{material}_pathway1.pkl"
# 【路径2】
# path_2 = "tree_files/pathway2.pkl"

tree_main = tree_loader.load_tree(tree_main_filename)
# tree_filtered = tree_loader.load_tree(tree_filtered_filename)
tree_wo_exp = tree_loader.load_tree(tree_wo_exp_filename)
path1_tree = tree_loader.load_tree(path_1)
# path2_tree = tree_loader.load_tree(path_2)

tree_main_api = create_tree_from_saved_tree(tree_main)
# tree_filtered_api = create_tree_from_saved_tree(tree_filtered)
tree_wo_exp_api = create_tree_from_saved_tree(tree_wo_exp)
path1_tree_api = create_tree_from_saved_tree(path1_tree)
# path2_tree_api = create_tree_from_saved_tree(path2_tree)


# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 路由：返回树结构的JSON
@app.get("/api/tree", response_model=Node)
async def get_tree():
    # return create_tree()
    # return api_tree
    return tree_main_api

# 路由：返回两个树
# @app.get("/api/double")
# async def get_double():
#     print("执行DOUBLE")
#     # return {
#     #     "bigTree": api_tree,
#     #     "smallTree": small_api_tree
#     # }
#     return {
#         "bigTree": tree_main_api,
#         "smallTree": tree_filtered_api
#     }

# 路由：返回四个树
# todo: 3 tree: wo_exp + w_exp + pathway
@app.get("/api/quad")
async def get_quadruple():
    print("执行QUADRUPLE")
    return {
        "main": tree_main_api,
        "son": tree_wo_exp_filename,
        "path1": path1_tree_api,
        # "path2": path2_tree_api
    }

# 路由：返回五个树
# @app.get("/api/five")
# async def get_five():
#     print("执行FIVE")
#     return {
#         "main": tree_main_api,
#         "son": tree_filtered_api,
#         "path1": path1_tree_api,
#         "path2": path2_tree_api,
#         "black_tree": tree_wo_exp_api
#     }


