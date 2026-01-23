import csv

def read_numbers(file_path):
    numbers = []
    with open(file_path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                numbers.append(int(row[0]))
    return numbers


def normalize(numbers):
    if not numbers:
        return []

    max_value = max(numbers)
    if max_value == 0:
        return numbers

    return [n / max_value for n in numbers]
