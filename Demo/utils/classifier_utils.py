def classify_numbers(numbers, threshold=0.5):
    labels = []
    for n in numbers:
        if n >= threshold:
            labels.append("HIGH")
        else:
            labels.append("LOW")
    return labels


class SimpleClassifier:
    def __init__(self, threshold):
        self.threshold = threshold

    def predict(self, numbers):
        return classify_numbers(numbers, self.threshold)
