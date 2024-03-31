from collections import deque


class ProtocolHierarchy:

    def __init__(self):

        self.extensions = {}

    def add_extension(self, extension, extended):

        if extended in self.extensions:
            self.extensions[extended].append(extension)
        else:
            self.extensions[extended] = [extension]

        return True, None

    def conforms(self, type_a, type_b):

        if type_a == type_b:
            return True

        if type_a in self.inheritances:
            return self.conforms(self.inheritances[type_a], type_b)

        return False

    def bfs_visit_order(self):
        visited_order = []
        queue = deque()
        visited = set()

        for node in self.extensions.keys():
            if node not in visited:
                queue.append(node)
                visited.add(node)

                while queue:
                    current_node = queue.popleft()
                    visited_order.append(current_node)

                    if current_node in self.extensions:
                        for child in self.extensions[current_node]:
                            if child not in visited:
                                queue.append(child)
                                visited.add(child)

        return visited_order
