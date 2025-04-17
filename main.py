import time
import random
import matplotlib.pyplot as plt
from BinaryTree import BTree, Buffer
from generate_records import get_key_by_line_index, generate_parallelogram_data

class BTreeConsoleInterface:
    def __init__(self, btree):
        self.b_tree = btree
        self.file_name = "record.txt"

    def display_menu(self):
        print("\nMenu główne:")
        print("1. Generuj rekordy do pliku")
        print("2. Dodaj rekordy z pliku do B-drzewa")
        print("3. Zarządzaj rekordami w B-drzewie (dodaj, usuń, aktualizuj)")
        print("4. Przeprowadź eksperyment")
        print("0. Wyjdź")

    def generate_records(self):
        min_records = int(input("Podaj minimalną liczbę rekordów: "))
        max_records = int(input("Podaj maksymalną liczbę rekordów: "))
        generate_parallelogram_data("record.txt", min_records, max_records, 3)
        print(f"Rekordy wygenerowane do pliku {self.file_name}.")

    def load_records_to_btree(self):
        if not self.b_tree:
            print("B-drzewo nie zostało jeszcze stworzone. Najpierw stwórz B-drzewo ręcznie.")
            return
        with open(self.file_name, 'r') as file:
            i = 1
            for line in file:
                parts = line.strip().split()
                key = int(parts[0])
                self.b_tree.insert(key, i)
                i += 1

        print("Rekordy zostały załadowane do B-drzewa.")
        self.b_tree.visualize_tree()
    def manage_records(self):
        if not self.b_tree:
            print("Tworzenie nowego B-drzewa...")
            degree = int(input("Podaj stopień B-drzewa: "))
            self.b_tree = BTree(degree)  # Zakładamy istnienie klasy BTree

        while True:
            print("\nZarządzanie rekordami w B-drzewie:")
            print("1. Dodaj rekord")
            print("2. Usuń rekord")
            print("3. Zaktualizuj rekord")
            print("4. Wyswietl drzewo")
            print("0. Powrót do menu głównego")

            choice = input("Wybierz opcję: ")
            if choice == "1":
                key = int(input("Podaj klucz do dodania: "))
                side1 = int(input("Podaj bok do dodania: "))
                side2 = int(input("Podaj bok do dodania: "))
                c = int(input("Podaj kat do dodania: "))
                #localization = int(k("Podaj adres do dodania: "))
                #self.b_tree.insert(key, key)
                self.b_tree.append_new_value(key,side1,side2,c)
                self.b_tree.visualize_tree()
                self.b_tree.traverse()
                print(f"Klucz {key} został dodany do B-drzewa.")
            elif choice == "2":
                key = int(input("Podaj klucz do usunięcia: "))
                self.b_tree.delete_key(key)
                self.b_tree.visualize_tree()
                self.b_tree.traverse()
                print(f"Klucz {key} został usunięty z B-drzewa.")
            elif choice == "3":
                print("1. Aktualizuj klucz rekordu")
                print("2. Aktualizuj lokalizacje rekordu")
                choice2 = input("Wybierz opcję: ")
                if choice2 == "1":
                    key = int(input("Podaj klucz do aktualizacji: "))
                    new_key = int(input("Podaj nową wartość klucza: "))
                    node, position = self.b_tree.search_key(self.b_tree.root.address, key)
                    self.b_tree.buffer.pages = []
                    localization = self.b_tree.get_localization(node, position)
                    if self.b_tree.delete_key(key) == False:
                        print(f"Klucz {key} nie został zaktualizowany.")
                    else:
                        self.b_tree.insert(new_key, localization)
                        self.b_tree.visualize_tree()
                        self.b_tree.traverse()
                        print(f"Klucz {key} został zaktualizowany na {new_key}.")
                elif choice2 == "2":
                    key = int(input("Podaj klucz do zmiany lokalizacji: "))
                    new_lokalization = int(input("Podaj nową wartość lokalizacji: "))
                    self.b_tree.actualize_tree(key, new_lokalization)
                    self.b_tree.visualize_tree()
                    self.b_tree.traverse()
                    print(f"Klucz {key} został zaktualizowany.")
                else:
                    print("Nieprawidłowy wybór")
            elif choice == "4":
                self.b_tree.visualize_tree()
                self.b_tree.traverse()
            elif choice == "0":
                break
            else:
                print("Nieprawidłowy wybór. Spróbuj ponownie.")

    def run_experiment(self):
        print("\nEksperymenty:")
        degrees = [2, 4, 6, 8, 10]
        record_counts = [10, 50, 100, 500, 1000, 5000]

        # Dane do globalnych wykresów
        degree_sums = {degree: {"reads": [], "writes": []} for degree in degrees}
        random_inserts = {degree: {"record_counts": [], "reads": [], "writes": []} for degree in degrees}

        for degree in degrees:
            print(f"\nTestowanie dla stopnia B-drzewa: {degree}")

            # Listy do przechowywania wyników dla danego stopnia
            record_sizes = []
            read_operations = []
            write_operations = []

            for record_count in record_counts:
                print(f"\n----------Liczba rekordów: {record_count}-----------")
                new_buff = Buffer(degree, "btree_data.bin", "record.txt")
                new_tree = BTree(degree, new_buff)

                if record_count > 100:
                    gen_values = 4
                else:
                    gen_values = 3

                generate_parallelogram_data("record.txt", record_count, record_count, gen_values)
                with open(self.file_name, 'r') as file:
                    i = 1
                    for line in file:
                        parts = line.strip().split()
                        key = int(parts[0])
                        new_tree.insert(key, i)
                        i += 1


                record_sizes.append(record_count)
                read_operations.append(new_buff.reads)
                write_operations.append(new_buff.writes)

                degree_sums[degree]["reads"].append(new_buff.reads)
                degree_sums[degree]["writes"].append(new_buff.writes)

                print(f"Zapisy: {new_buff.writes} Odczyty: {new_buff.reads}")
                new_buff.reads = 0
                new_buff.writes = 0

                plt.figure(figsize=(10, 6))
                plt.plot(record_sizes, read_operations, label="Operacje odczytu", marker='o', color='blue')
                plt.plot(record_sizes, write_operations, label="Operacje zapisu", marker='o', color='orange')
                plt.xlabel("Liczba rekordów")
                plt.ylabel("Liczba operacji")
                plt.title(f"Operacje odczytu i zapisu w B-drzewie (Stopień: {degree})")
                plt.legend()
                plt.grid(True)
                plt.show()

                random_key = random.randint(1, record_count)
                print(f"\nDodawanie losowego rekordu ({random_key}) do drzewa o stopniu {degree}...")
                new_tree.insert(random_key, i)
                print(f"Zapisy: {new_buff.writes} Odczyty: {new_buff.reads}\n")

                random_inserts[degree]["record_counts"].append(record_count)
                random_inserts[degree]["reads"].append(new_buff.reads)
                random_inserts[degree]["writes"].append(new_buff.writes)

                new_buff.reads = 0
                new_buff.writes = 0

        plt.figure(figsize=(10, 6))
        for degree in degrees:
            plt.scatter(random_inserts[degree]["record_counts"], random_inserts[degree]["reads"],
                        label=f"Odczyty (Stopień: {degree})", marker='o')
            plt.scatter(random_inserts[degree]["record_counts"], random_inserts[degree]["writes"],
                        label=f"Zapisy (Stopień: {degree})", marker='x')
        plt.xlabel("Liczba rekordów")
        plt.ylabel("Liczba operacji")
        plt.title("Operacje odczytu i zapisu dla dodania losowego elementu")
        plt.legend()
        plt.grid(True)
        plt.show()

        print("Eksperyment zakończony.")
    def run(self):
        while True:
            self.display_menu()
            choice = input("Wybierz opcję: ")
            if choice == "1":
                self.generate_records()
            elif choice == "2":
                self.load_records_to_btree()
            elif choice == "3":
                self.manage_records()
            elif choice == "4":
                self.run_experiment()
            elif choice == "0":
                print("Zamykam program. Do widzenia!")
                break
            else:
                print("Nieprawidłowy wybór. Spróbuj ponownie.")



if __name__ == "__main__":
    with open("btree_data.bin", "wb") as f:
        binary_data = b"\x48\x65\x6C\x6C\x6F"
        f.write(binary_data)
        pass
    D = 2
    buff = Buffer(D, "btree_data.bin", "record2.txt")
    tree = BTree(D, buff)
    interface = BTreeConsoleInterface(tree)
    interface.run()
