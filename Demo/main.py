from utils.data_utils import read_numbers, normalize
from utils.classifier_utils import SimpleClassifier

def main():
    numbers = read_numbers("data.csv")
    normalized = normalize(numbers)

    classifier = SimpleClassifier(threshold=0.6)
    labels = classifier.predict(normalized)

    for n, label in zip(numbers, labels):
        print(n, "->", label)


if __name__ == "__main__":
    main()
