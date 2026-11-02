"""The category tree and its recursive functions."""


class CategoryNode:
    def __init__(self, name):
        self.name = name
        self.children = {}      # name -> CategoryNode
        self.own_items = 0      # titles filed directly in this category


def build_tree(items, root_name="Library"):
    root = CategoryNode(root_name)
    for item in items:
        node = root
        path = [item.parent_category, item.category] if item.parent_category else [item.category]
        for name in path:
            node = node.children.setdefault(name, CategoryNode(name))
        node.own_items += 1
    return root


def total_items(node):
    """Base case: a node with no children is its own count. Smaller problem: each child."""
    return node.own_items + sum(total_items(child) for child in node.children.values())


def tree_lines(node, depth=0):
    lines = [f"{'  ' * depth}{node.name} ({total_items(node)})"]
    for name in sorted(node.children):
        lines.extend(tree_lines(node.children[name], depth + 1))
    return lines


def print_tree(root):
    print("\n".join(tree_lines(root)))


def find(node, name):
    if node.name == name:
        return node
    for child in node.children.values():
        found = find(child, name)
        if found is not None:
            return found
    return None


def count_items(root, name):
    node = find(root, name)
    return total_items(node) if node else 0


def path_to(node, name):
    """Return the list of names from `node` down to `name`, or None."""
    if node.name == name:
        return [name]
    for child_name in sorted(node.children):
        below = path_to(node.children[child_name], name)
        if below is not None:
            return [node.name] + below
    return None


def count_items_iter(root, name):
    """Iterative version: an explicit stack replaces the call stack (safe at any depth)."""
    node = find_iter(root, name)
    if node is None:
        return 0
    total, stack = 0, [node]
    while stack:
        current = stack.pop()
        total += current.own_items
        stack.extend(current.children.values())
    return total


def find_iter(root, name):
    stack = [root]
    while stack:
        current = stack.pop()
        if current.name == name:
            return current
        stack.extend(current.children.values())
    return None
