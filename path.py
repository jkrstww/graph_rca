import json
from collections import defaultdict


def load_json_data(file_path):
    """加载JSON文件数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_graph(data):
    """构建有向图"""
    graph = defaultdict(list)
    nodes = set()

    # 添加所有节点和边
    for item in data:
        effect = item['effect']
        nodes.add(effect)
        for cause in item['cause']:
            nodes.add(cause)
            graph[effect].append(cause)  # effect指向cause

    return graph, nodes


def find_start_nodes(graph, nodes):
    """找到起始节点（没有入边的节点）"""
    # 计算每个节点的入度
    in_degree = {node: 0 for node in nodes}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    # 返回入度为0的节点
    return [node for node in nodes if in_degree[node] == 0]


def dfs(graph, node, path, all_paths, visited):
    """深度优先遍历"""
    # 将当前节点添加到路径中
    path.append(node)
    visited.add(node)

    # 如果当前节点没有出边，保存路径
    if node not in graph or not graph[node]:
        all_paths.append('<-'.join(path))
    else:
        # 递归访问所有邻居节点
        for neighbor in graph[node]:
            if neighbor not in visited:  # 避免循环
                dfs(graph, neighbor, path.copy(), all_paths, visited.copy())

    # 回溯
    path.pop()
    visited.remove(node)


def find_all_paths(graph, nodes):
    """找到所有可能的路径"""
    # 找到起始节点
    start_nodes = find_start_nodes(graph, nodes)

    all_paths = []
    for start_node in start_nodes:
        dfs(graph, start_node, [], all_paths, set())

    return all_paths


def main():
    # 加载数据
    data = load_json_data('./graph/graph.json')  # 替换为你的JSON文件路径

    # 构建图
    graph, nodes = build_graph(data)

    # 找到所有路径
    paths = find_all_paths(graph, nodes)

    # 格式化输出
    result = []
    for i, path in enumerate(paths, 1):
        result.append({
            'id': i,
            'path': path
        })

    # 输出结果
    with open('./graph/path.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    f.close()


if __name__ == '__main__':
    main()