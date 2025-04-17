import random


def generate_parallelogram_data(file_name: str, min_records: int, max_records: int, num_digits: int):
    num_records = random.randint(min_records, max_records)
    used_keys = set()

    with open(file_name, 'w') as file:
        for _ in range(num_records):
            while True:
                key = random.randint(1, pow(10, num_digits) - 1)  # Klucz w zakresie 1 do 999
                if key not in used_keys:
                    used_keys.add(key)
                    break


            side1 = random.randint(1, 999)
            side2 = random.randint(1, 999)
            angle = random.randint(1, 179)


            key_str = f"{key:0{num_digits}d}"
            side1_str = f"{side1:0{num_digits}d}"  # Bok1: 3 cyfry z wypełnieniem 0
            side2_str = f"{side2:0{num_digits}d}"  # Bok2: 3 cyfry z wypełnieniem 0
            angle_str = f"{angle:0{num_digits}d}"  # Kąt: 3 cyfry z wypełnieniem 0

            file.write(f"{key_str} {side1_str} {side2_str} {angle_str}\n")

def get_key_by_line_index(file_name: str, line_index: int):
    with open(file_name, 'r') as file:
        for current_index, line in enumerate(file):
            if current_index == line_index:
                return int(line.split()[0])
    raise ValueError(f"Linia o indeksie {line_index} nie istnieje w pliku.")

