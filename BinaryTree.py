import struct
import os


T_SIZE = 2

class BTreeNode:
    def __init__(self, t, address=None):
        self.t = t  # Minimalny stopień drzewa
        self.keys = []  # Klucze w węźle
        self.children = []  # Wskaźniki na dzieci (adresy w pliku)
        self.localization = []
        self.parent = None  # Wskaźnik na rodzica (adres w pliku)
        self.address = address  # Adres w pliku
        self.is_leaf = True  # Czy węzeł jest liściem?

    def printNode(self):
        print(self.keys, self.children, self.localization)

class Buffer:
    def __init__(self, t, file_name, general_file):
        self.page_size = self.calculate_page_size(t)  # Obliczanie rozmiaru strony na podstawie t
        self.file_name = file_name
        self.general_file = general_file
        self.pages = []  # Struktura przechowująca wczytane strony
        self.writes = 0
        self.reads = 0
        self.t = t

    @staticmethod
    def calculate_page_size(t):
        max_keys = t * 2
        max_children = t * 2 + 1
        max_localization = t * 2
        return max_keys * 4 + max_children * 4 + max_localization * 4 + 4 + 4

    def read_node(self, address):
        """Wczytuje węzeł z pliku na podstawie adresu."""
        with open(self.file_name, 'rb') as f:
            f.seek(address)
            data = f.read(self.page_size)
        return self.deserialize_node(data, address, self.t)

    def write_node(self, node):
        """Zapisuje węzeł do pliku na podstawie jego adresu."""
        serialized_data = self.serialize_node(node)
        with open(self.file_name, 'r+b') as f:
            f.seek(node.address)
            f.write(serialized_data)

    def allocate_address(self):
        """Przydziela nowy adres na podstawie końca pliku."""
        with open(self.file_name, 'ab') as f:
            f.seek(0, 2)  # Przejdź na koniec pliku
            return f.tell()

    def replace_node(self, address, new_node):
        """Podmienia zawartość istniejącego węzła w pliku."""
        new_node.address = address
        self.write_node(new_node)

    @staticmethod
    def serialize_node(node):
        max_keys = 2 * node.t
        max_localization = 2 * node.t
        max_children = 2 * node.t + 1

        keys = node.keys + [0] * (max_keys - len(node.keys))
        localization = node.localization + [0] * (max_localization - len(node.localization))
        children = node.children + [0] * (max_children - len(node.children))

        return struct.pack(
            f'{max_keys}i {max_children}i {max_localization}i ? i',
            *keys,  # Klucze
            *children,  # Dzieci
            *localization, #Lokalizacja w pliku głównym
            node.is_leaf,  # Czy liść
            node.parent if node.parent is not None else 0  # Wskaźnik rodzica
        )

    @staticmethod
    def deserialize_node(data, address, t):

        max_keys = 2 * t  # Liczba kluczy obliczana na podstawie rozmiaru
        max_children = 2 * t + 1
        max_localization = 2 * t

        expected_size = struct.calcsize(f'{max_keys}i {max_children}i {max_localization}i ? i')
        if len(data) != expected_size:
            raise ValueError(
                f"Rozmiar danych ({len(data)}) nie pasuje do oczekiwanego rozmiaru ({expected_size})"
            )


        unpacked_data = struct.unpack(
            f'{max_keys}i {max_children}i {max_localization}i ? i',
            data
        )


        keys = [key for key in unpacked_data[:max_keys] if key != 0]
        children = [child for child in unpacked_data[max_keys:max_keys + max_children] if child != 0]
        localizations = [localization for localization in unpacked_data[max_keys + max_children:max_keys + max_children + max_localization] if localization != 0]


        is_leaf = unpacked_data[max_keys + max_children + max_localization ]
        parent = unpacked_data[max_keys + max_children + max_localization + 1]



        node = BTreeNode(t, address=address)
        node.keys = keys
        node.children = children
        node.localization = localizations
        node.is_leaf = is_leaf
        node.parent = parent if parent != 0 else None
        return node


class BTree:
    def __init__(self, t=2, buffer=None):
        self.t = t
        self.buffer = buffer
        root_address = self.buffer.allocate_address()
        self.root = BTreeNode(t, address=root_address)
        self.buffer.write_node(self.root)


    def read_line_and_parse(self, line_number, file_path):
        with open(file_path, 'r') as file:
            for current_line_number, line in enumerate(file):
                if current_line_number == line_number:
                    numbers = list(map(int, line.split()))
                    if len(numbers) != 4:
                        raise ValueError("Linia nie zawiera dokładnie 4 wartości liczbowych.")

                    # Tworzenie słownika z danymi
                    return {
                        'key_number': numbers[0],
                        'side_a': numbers[1],
                        'side_b': numbers[2],
                        'angle': numbers[3]
                    }
        raise ValueError("Linia o podanym numerze nie istnieje.")

    def get_localization(self, node,i):
        return node.localization[i]

    def get_child_number_in_parent(self, parent, child):
        for i in range(0, len(parent.children)):
            if child.address == parent.children[i]:
                return i

        print("Nie znaleziono dziecka w rodzicu - to błąd")
        return None

    def get_last_line_number(self):
        try:
            with open(self.buffer.general_file, "r") as file:
                lines = file.readlines()
                return len(lines)
        except FileNotFoundError:
            print(f"Plik '{self.buffer.general_file}' nie istnieje.")
            return 0
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return -1

    def write_new_value(self, values):
        formatted_values = [f"{value:03}" for value in values]
        new_line = " ".join(formatted_values) + "\n"
        with open(self.buffer.general_file, "a") as file:
            file.write(new_line)

    def where_insert(self,node, key):
        i = 0
        if len(node.keys) != 0:
            while i < len(node.keys):
                if node.keys[i] > key:
                    return i
                i += 1
        return i

    def search_key(self, node_address, key):
        node = self.buffer.read_node(node_address)  # Wczytaj bieżący węzeł
        self.buffer.reads += 1
        self.buffer.pages.append(node)

        for i, k in enumerate(node.keys):
            if k == key:
                return node, i

            if key < k:
                if not node.is_leaf:
                    return self.search_key(node.children[i], key)
                else:
                    #print("Nie znaleziono klucza")
                    return node, i


        if not node.is_leaf:
            return self.search_key(node.children[-1], key)

        #print("Nie znaleziono kluczaaa")
        return node, -1

    def actualize_tree(self, key, new_localization):
        """ aktualizuje tylko lokalizacje"""
        node, i = self.search_key(self.root.address, key)
        node.localization[i] = new_localization
        self.buffer.write_node(node)

    def insert(self, key, localization):
        node = self._insert_non_full(self.root, key, localization)  # Wstawienie klucza
        if node != None and node.address == self.root.address:
            self.root = node
        self.buffer.pages = []


    def append_new_value(self, key, side1, side2, angle):
        localization = self.get_last_line_number()
        node = self._insert_non_full(self.root, key, localization)  # Wstawienie klucza
        if node != None and node.address == self.root.address:
            self.root = node
        if node != None:
            values = [key, side1, side2, angle]
            self.write_new_value(values)
            print(f"---WARTOSC KLUCZA {key} DODANA POMYSLNIE---")
        else:
            print(f"---WARTOSC KLUCZA {key} JUZ ZNAJDUJE SIE W DRZEWIE---")

    def _insert_non_full(self, node, key, localization):
        found_node, i = self.search_key(node.address, key)

        if len(found_node.keys) == 0:   #brak kluczy mozna wstawic do roota
            found_node.keys.append(key)
            found_node.localization.append(localization)
            self.buffer.write_node(found_node)
            self.buffer.writes += 1
            return found_node

        if found_node.keys[i] == key:
            print("Klucz istnieje nie mozna go wstawic")
            return None

        if len(found_node.keys) == (2 * self.t):  # Jeśli liść jest pełny
            parent_address = found_node.parent
            if parent_address is not None:
                parent = self.buffer.read_node(parent_address)

                if self.compensation(parent, found_node, i,  key, localization): #kompensacja
                    return found_node

                self.split_child(parent, found_node, key, localization)
            else:
                self.split_root(key, localization, None)  # Rozszczepienie korzenia
                return found_node
        else:
            place = self.where_insert(found_node, key)
            found_node.keys.insert(place,key)  # Dodaj klucz do liścia
            found_node.localization.insert(place,localization)
            self.buffer.write_node(found_node)
            self.buffer.writes += 1
            return found_node


    def compensation(self, parent, child, place, key, localization):
        i = 0
        while i < len(parent.children):
            if parent.children[i] == child.address:
                break
            i += 1


        if i == 0:  # Brother is on the right only
            #print("Brother on the right ")
            brother_address = parent.children[i + 1]
            brother = self.buffer.read_node(brother_address)
            self.buffer.reads += 1

            if len(brother.keys) < 2 * self.t:
                #print("Brother on the right  noew ",  brother.keys)
                place = self.where_insert(child,key)
                child.keys.insert(place,key)
                child.localization.insert(place,key)
                #child.keys.append(key)
                #child.keys.sort()
                key_to_parent = child.keys.pop()
                localization_to_parent = child.localization.pop()

                key_to_brother = parent.keys[i]
                localization_to_brother = parent.localization[i]
                parent.keys[i] = key_to_parent
                parent.localization[i] = localization_to_parent

                brother.keys.insert(0, key_to_brother)
                brother.localization.insert(0, localization_to_brother)
            else:
                return None

        elif i == len(parent.children) - 1:  # Brother is on the left only
            #print("Brother on the left ")
            brother_address = parent.children[i - 1]
            brother = self.buffer.read_node(brother_address)
            self.buffer.reads += 1

            if len(brother.keys) < 2 * self.t:
                place = self.where_insert(child, key)
                child.keys.insert(place,key)
                child.localization.insert(place,key)
                key_to_parent = child.keys.pop(0)
                localization_to_parent = child.localization.pop(0)
                key_to_brother = parent.keys[i - 1]
                localization_to_brother = parent.localization[i - 1]
                parent.keys[i - 1] = key_to_parent
                parent.localization[i - 1] = localization_to_parent

                brother.keys.append(key_to_brother)
                brother.localization.append(localization_to_brother)
            else:
                return None

        else:  # Both left and right brothers exist
            left_brother_address = parent.children[i - 1]
            left_brother = self.buffer.read_node(left_brother_address)

            right_brother_address = parent.children[i + 1]
            right_brother = self.buffer.read_node(right_brother_address)
            self.buffer.reads += 1

            if len(left_brother.keys) < 2 * self.t:
                place = self.where_insert(child, key)
                child.keys.insert(place,key)
                child.localization.insert(place,key)
                key_to_parent = child.keys.pop(0)
                localization_to_parent = child.localization.pop(0)
                key_to_brother = parent.keys[i - 1]
                localization_to_brother = parent.localization[i - 1]
                parent.keys[i - 1] = key_to_parent
                parent.localization[i - 1] = localization_to_parent

                left_brother.keys.append(key_to_brother)
                left_brother.localization.append(localization_to_brother)
                brother = left_brother

            elif len(right_brother.keys) < 2 * self.t:
                place = self.where_insert(child, key)
                child.keys.insert(place,key)
                child.localization.insert(place,key)
                key_to_parent = child.keys.pop()
                localization_to_parent = child.localization.pop()

                key_to_brother = parent.keys[i]
                localization_to_brother = parent.localization[i]
                parent.keys[i] = key_to_parent
                parent.localization[i] = localization_to_parent

                right_brother.keys.insert(0, key_to_brother)
                right_brother.localization.insert(0, localization_to_brother)
                brother = right_brother
            else:
                return None

        if parent.address == self.root.address:
            self.root = parent

        self.buffer.write_node(brother)
        self.buffer.writes += 1
        self.buffer.write_node(parent)
        self.buffer.writes += 1
        self.buffer.write_node(child)
        self.buffer.writes += 1

        return True

    def split_root(self, key, localization, node):
        if node != None:
            if self.root.address == node.address:
                root = node
            else:
                print("Root is not the node but it was given")
                root = self.root
        else:
            root = self.root
        new_root_address = self.buffer.allocate_address()
        new_root = BTreeNode(self.t, address=new_root_address)
        new_root.children.append(root.address)
        new_root.is_leaf = False
        self.root = new_root
        root.parent = new_root_address
        self.buffer.write_node(new_root)
        #print(root.address, new_root.address)
        self.split_child(new_root, root, key, localization)
    def split_child(self, parent, node, key, localization):
        t = self.t
        if node == None:
            child = parent.children[0]
        else:
            child = node

        index = parent.children.index(node.address)
        new_child_address = self.buffer.allocate_address()
        new_child = BTreeNode(t, address=new_child_address)
        new_child.is_leaf = child.is_leaf
        new_child.parent = parent.address
        place = self.where_insert(child, key)
        child.keys.insert(place,key)
        child.localization.insert(place, localization)
        middle = (len(child.keys)//2)
        mid_key = child.keys.pop(middle)  # Środkowy klucz
        #print(child.localization)
        mid_loc = child.localization.pop(middle)
        #print("During splitting the mid key is ", mid_key)
        parent.children.insert(index + 1, new_child_address)
        new_child.keys = child.keys[middle:]
        child.keys = child.keys[:middle]
        new_child.localization = child.localization[middle:]
        child.localization = child.localization[:middle]

        if not child.is_leaf:
            new_child.children = child.children[middle+1:]
            child.children = child.children[:middle+1]
            for childer in new_child.children:
                childeree = self.buffer.read_node(childer)
                self.buffer.reads += 1
                childeree.parent = new_child.address
                self.buffer.write_node(childeree)
                self.buffer.writes += 1

        self.buffer.write_node(child)
        self.buffer.writes += 1
        self.buffer.write_node(new_child)
        self.buffer.writes += 1

        #print("child", child.address, child.keys, child.localization, child.children)
        #print("new_child",new_child.address ,  new_child.keys, new_child.localization, new_child.children)
        #print("parent", parent.address , parent.keys, parent.localization, parent.children)
        #parent.keys.insert(index, mid_key)

        if len(parent.keys) == (2 * self.t):
            if parent.address == self.root.address:
                self.split_root(mid_key, mid_loc, parent)
            else:
                new_parent_address = parent.parent
                new_parent = self.buffer.read_node(new_parent_address)

                self.split_child(new_parent, parent, mid_key, mid_loc)
        else:
            parent.keys.insert(index, mid_key)
            parent.localization.insert(index, mid_loc)
            if parent.address == self.root.address:
                self.root = parent
            self.buffer.write_node(parent)
            self.buffer.writes += 1

    def get_position_in_pages(self, address):
        for i in range(len(self.buffer.pages)):
            if self.buffer.pages[i].address == address:
                return i

        print("Nie odnaleziono pozycji w pages")

    def delete_key(self, key):
        ret = self.delete(self.root, key)
        self.buffer.pages = []
        if ret != None:
            return True
        else:
            return False
    def delete(self, node, key):
        # 1. Szukaj klucz
        found_node, i = self.search_key(node.address, key)

        # 2. Jeśli klucz nie został znaleziony
        if found_node.keys[i] != key:
            print("Klucz nie został znaleziony i nie mozna go usunac.")
            return None

        # 3. Klucz znajduje się na stronie
        if key in found_node.keys:
            # 4a sprawdzamy czy lisc
            if found_node.is_leaf:
                found_node.keys.remove(key)
                del found_node.localization[i]

                if len(found_node.keys) >= self.t:
                    self.buffer.write_node(found_node)
                    return found_node
                else:
                    return self._handle_underflow(found_node)
            else:
                prev = self.buffer.read_node(found_node.children[i])
                post = self.buffer.read_node(found_node.children[i + 1])

                if len(prev.keys) >= self.t:
                    predecessor_node = self._get_predecessor(found_node, i)
                    found_node.keys[i] = predecessor_node.keys.pop()
                    found_node.localization[i] = predecessor_node.localization.pop()
                    self.buffer.write_node(found_node)
                    self.buffer.write_node(predecessor_node)
                    if len(predecessor_node.keys) < self.t:
                        place = self.get_position_in_pages(found_node.address)
                        self.buffer.pages[place] = found_node
                        self._handle_underflow(predecessor_node)
                    else:
                        self.buffer.write_node(predecessor_node)
                        return True


                elif len(post.keys) >= self.t:
                    successor_node = self._get_successor(found_node, i)
                    found_node.keys[i] = successor_node.keys.pop()
                    found_node.localization[i] = successor_node.localization.pop()
                    self.buffer.write_node(found_node)
                    self.buffer.write_node(successor_node)
                    if len(successor_node.keys) < self.t:
                        place = self.get_position_in_pages(found_node.address)
                        self.buffer.pages[place] = found_node
                        self._handle_underflow(successor_node)
                    else:
                        self.buffer.write_node(successor_node)
                        return True

                else:
                    self._merge_children(found_node, i)
                    return self.delete(found_node.children[i], key)

        return True


    def _handle_underflow(self, node, child_index=None):
        if len(self.buffer.pages) > 1:  #sprawdzamy czy jest rodzic w buforze
            parent = self.buffer.pages[-2]
            child = node
            position = self.get_child_number_in_parent(parent, child)

            if position > 0:
                left_sibling = self.buffer.read_node(parent.children[position - 1])
                if len(left_sibling.keys) > self.t:
                    self._compensate_from_left(parent, child, left_sibling, position)
                    return True

            if position < len(parent.children) - 1:
                right_sibling = self.buffer.read_node(parent.children[position + 1])
                if len(right_sibling.keys) > self.t:
                    self._compensate_from_right(parent, child, right_sibling, position)
                    return True

            self.buffer.write_node(node)
            if position > 0:
                self._merge_children(parent, position - 1)
            else:
                self._merge_children(parent, position)

        else:   #przypadek tylko dla roota
            if node.is_leaf and node.address == self.root.address:
                self.buffer.write_node(node)

        return True

    def _compensate_from_left(self, parent, child, left_sibling, child_index):

        if len(child.keys) > 0:
            child.keys.insert(0, parent.keys[child_index - 1])
            child.localization.insert(0, parent.localization[child_index - 1])
        else:
            child.keys.append(parent.keys[child_index - 1])
            child.localization.append(parent.localization[child_index - 1])

        parent.keys[child_index - 1] = left_sibling.keys.pop()
        parent.localization[child_index - 1] = left_sibling.localization.pop()

        if not child.is_leaf:
            child.children.insert(0, left_sibling.children.pop())
            new = self.buffer.read_node(child.children[-1])
            new.parent = child.address
            self.buffer.write_node(new)

        self.buffer.write_node(left_sibling)
        self.buffer.write_node(child)
        self.buffer.write_node(parent)

    def _compensate_from_right(self, parent, child, right_sibling, child_index):

        child.keys.append(parent.keys[child_index])
        child.localization.append(parent.localization[child_index])

        parent.keys[child_index] = right_sibling.keys.pop(0)
        parent.localization[child_index] = right_sibling.localization.pop(0)

        if not child.is_leaf:
            child.children.append(right_sibling.children.pop(0))
            new = self.buffer.read_node(child.children[-1])
            new.parent = child.address
            self.buffer.write_node(new)

        self.buffer.write_node(right_sibling)
        self.buffer.write_node(child)
        self.buffer.write_node(parent)

    def _merge_children(self, parent, index):

        left_child = self.buffer.read_node(parent.children[index])
        right_child = self.buffer.read_node(parent.children[index + 1])


        left_child.keys.append(parent.keys.pop(index))
        left_child.localization.append(parent.localization.pop(index))


        left_child.keys.extend(right_child.keys)
        left_child.localization.extend(right_child.localization)
        for temp_child_addr in right_child.children:
            temp_child = self.buffer.read_node(temp_child_addr)
            temp_child.parent = left_child.address
            self.buffer.write_node(temp_child)
        left_child.children.extend(right_child.children)

        parent.children.pop(index + 1)
        #print("left:")
        #left_child.printNode()
        #print("parent:")
        #parent.printNode()
        self.buffer.write_node(left_child)
        self.buffer.write_node(parent)

        if len(parent.keys) == 0 and parent.address == self.root.address:
            left_child.parent = None
            self.root = left_child
            self.buffer.write_node(self.root)
            #print("to sa dzieci", left_child.children, left_child.is_leaf)
        elif len(parent.keys) < self.t and parent.address != self.root.address:
            self.buffer.pages.pop()
            self._handle_underflow(parent)


    # Pomocnicze metody do znajdowania poprzednika i następcy
    def _get_predecessor(self, node, index):
        current = self.buffer.read_node(node.children[index])
        self.buffer.pages.append(current)
        while not current.is_leaf:
            current = self.buffer.read_node(current.children[-1])
            self.buffer.pages.append(current)
        return current

    def _get_successor(self, node, index):
        current = self.buffer.read_node(node.children[index + 1])
        self.buffer.pages.append(current)
        while not current.is_leaf:
            current = self.buffer.read_node(current.children[0])
            self.buffer.pages.append(current)
        return current

    def traverse(self):
        self._traverse_node(self.root, 0)

    def _traverse_node(self, node, deep):
        if node.is_leaf:
            print(f"{'-' * deep}Node {node.address}: {node.keys} children:{node.children}, localizaton:{node.localization}")
        else:
            for i, key in enumerate(node.keys):
                self._traverse_node(self.buffer.read_node(node.children[i]), deep + 1)
            self._traverse_node(self.buffer.read_node(node.children[-1]), deep + 1)
            print(f"{'-' * deep}Node {node.address}: {node.keys} children:{node.children}, localizaton:{node.localization}")

    def visualize_tree(self):
        import matplotlib.pyplot as plt
        import networkx as nx

        G = nx.DiGraph()
        pos = {}
        self._add_nodes_edges(self.buffer.read_node(self.root.address), G, pos, 0, 0, 1)

        plt.figure(figsize=(12, 4))
        nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue",
                font_size=7, font_weight="bold", font_color="black")
        plt.show()

    def _add_nodes_edges(self, node, G, pos, x, y, width):
        if node is None:
            return

        node_label = f"{node.keys}"  # Klucze w węźle
        G.add_node(node_label)  # Dodaj węzeł do grafu
        pos[node_label] = (x, y)  # Pozycja węzła

        if node.children:
            step = width / len(node.children)
            for i, child_address in enumerate(node.children):
                child = self.buffer.read_node(child_address)
                child_x = x - width / 2 + step * (i + 0.5)  # Pozycja X dziecka
                child_y = y - 1  # Pozycja Y (niższy poziom)
                self._add_nodes_edges(child, G, pos, child_x, child_y, step)  # Rekurencja
                G.add_edge(node_label, f"{child.keys}")  # Dodaj krawędź


'''
with open("btree_data.bin", "wb") as f:
    binary_data = b"\x48\x65\x6C\x6C\x6F"
    # Example binary data
    f.write(binary_data)
    pass



buff = Buffer(2, "btree_data.bin", "record.txt")
tree = BTree(2, buff)
for i in range(1,30):
    print("To jest próba: ", i)
    if i != 45 and i != 49:
        tree.insert(i,i)
    if i > 27:
        tree.visualize_tree()


tree.delete(tree.root, 15)
tree.visualize_tree()
tree.delete(tree.root, 14)
tree.visualize_tree()
tree.delete(tree.root, 13)
tree.visualize_tree()
tree.traverse()
                
'''