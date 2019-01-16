"""Code to accompany Machine Learning Recipes #8.

We'll write a Decision Tree Classifier, in pure Python.
"""

import sys
import csv
from random import shuffle


def import_dataset(filepath, delimiter=';'):
    """Import a csv file to a list."""
    with open(filepath, mode='r') as f:
        reader = csv.reader(f, delimiter=delimiter)
        data = list(reader)
        header = [b for a in data[0:1] for b in a]
        return data[1:], header


def split_data(data, partition=0.7):
    """Split list into two chunks."""
    shuffle(data)
    return data[0: int(len(data) * partition)], data[int(len(data) * partition):]


data, header = import_dataset(sys.argv[1])


def unique_vals(rows, col):
    """Find the unique values for a column in a dataset."""
    return set([row[col] for row in rows])


def class_counts(rows):
    """Counts the number of each type of example in a dataset."""
    counts = {}  # a dictionary of label -> count.
    for row in rows:
        # in our dataset format, the label is always the last column
        label = row[-1]
        if label not in counts:
            counts[label] = 0
        counts[label] += 1
    return counts


def is_numeric(value):
    """Test if a value is numeric."""
    return isinstance(value, int) or isinstance(value, float)


class Question:
    """A Question is used to partition a dataset.

    This class just records a 'column number' (e.g., 0 for Color) and a
    'column value' (e.g., Green). The 'match' method is used to compare
    the feature value in an example to the feature value stored in the
    question. See the demo below.
    """

    def __init__(self, column, value):
        self.column = column
        self.value = value

    def match(self, example):
        # Compare the feature value in an example to the
        # feature value in this question.
        val = example[self.column]
        if is_numeric(val):
            return val >= self.value
        else:
            return val == self.value

    def __repr__(self):
        # This is just a helper method to print
        # the question in a readable format.
        condition = "=="
        if is_numeric(self.value):
            condition = ">="
        return "Is %s %s %s?" % (
            header[self.column], condition, str(self.value))


def partition(rows, question):
    """Partitions a dataset.

    For each row in the dataset, check if it matches the question. If
    so, add it to 'true rows', otherwise, add it to 'false rows'.
    """
    true_rows, false_rows = [], []
    for row in rows:
        if question.match(row):
            true_rows.append(row)
        else:
            false_rows.append(row)
    return true_rows, false_rows


def P(val, pos):
    N = sum(map(lambda x: x[1], pos))
    return (val/N)


def gini_index(x):
    N = len(x)
    try:
        return (1-reduce(lambda a, b: (P(a[1], x)**2) + (P(b[1], x)**2), x)) / (N/(N-1))
    except:
        return 0


def entropia(x):
    N = len(x)
    try:
        return (-reduce(lambda a, b: P(a[1], x)*log(P(a[1], x), 2) + P(b[1], x)*log(P(b[1], x), 2), x)) * (1 / (log(N, 2)))
    except:
        return 0


def missclassification(x):
    N = len(x)
    try:
        return (1 - max(list(map(lambda l: P(l[1], x), x)))) / (N/(N-1))
    except:
        return 0


def generalized_gini_index(x):
    return missclassification(x)


def MaxDiffNormalized(x):
    N = len(x)
    try:
        X = (max(list(map(lambda l:  P(l[1], x) - (1 - P(l[1], x)), x)))) / N
        return X + (0.5 * (1-X))
    except:
        return 0


def impurity(rows):
    """Calculate the Impurity for a list of rows.

    Based on this example:
    https://en.wikipedia.org/wiki/Decision_tree_learning#Gini_impurity
    """

    counts = class_counts(rows)
    impurity = 1
    for lbl in counts:
        prob_of_lbl = counts[lbl] / float(len(rows))
        impurity -= prob_of_lbl**2
    return impurity


def info_gain(left, right, current_uncertainty):
    """Information Gain.

    The uncertainty of the starting node, minus the weighted impurity of
    two child nodes.
    """
    p = float(len(left)) / (len(left) + len(right))
    return current_uncertainty - p * impurity(left) - (1 - p) * impurity(right)


def info_gain_iter(rows):
    return missclassification(rows)


def find_best_split(rows):
    """Find the best question to ask by iterating over every feature / value
    and calculating the information gain."""
    best_gain = 0  # keep track of the best information gain
    best_question = None  # keep train of the feature / value that produced it
    current_uncertainty = impurity(rows)
    n_features = len(rows[0]) - 1  # number of columns

    for col in range(n_features):  # for each feature

        values = set([row[col] for row in rows])  # unique values in the column

        for val in values:  # for each value

            question = Question(col, val)

            # try splitting the dataset
            true_rows, false_rows = partition(rows, question)

            # Skip this split if it doesn't divide the
            # dataset.
            if len(true_rows) == 0 or len(false_rows) == 0:
                continue

            # Calculate the information gain from this split
            gain = info_gain(true_rows, false_rows, current_uncertainty)
            # gain = info_gain_iter(rows)  # MaxDiffNormalized

            # You actually can use '>' instead of '>=' here
            # but I wanted the tree to look a certain way for our
            # toy dataset.
            if gain >= best_gain:
                best_gain, best_question = gain, question

    return best_gain, best_question


class Leaf:
    """A Leaf node classifies data.

    This holds a dictionary of class (e.g., "Apple") -> number of times
    it appears in the rows from the training data that reach this leaf.
    """

    def __init__(self, rows):
        self.predictions = class_counts(rows)


class Decision_Node:
    """A Decision Node asks a question.

    This holds a reference to the question, and to the two child nodes.
    """

    def __init__(self,
                 question,
                 true_branch,
                 false_branch):
        self.question = question
        self.true_branch = true_branch
        self.false_branch = false_branch


def build_tree(rows):
    """Builds the tree.

    Rules of recursion: 1) Believe that it works. 2) Start by checking
    for the base case (no further information gain). 3) Prepare for
    giant stack traces.
    """

    # Try partitioning the dataset on each of the unique attribute,
    # calculate the information gain,
    # and return the question that produces the highest gain.
    gain, question = find_best_split(rows)

    # Base case: no further info gain
    # Since we can ask no further questions,
    # we'll return a leaf.
    if gain == 0:
        return Leaf(rows)

    # If we reach here, we have found a useful feature / value
    # to partition on.
    true_rows, false_rows = partition(rows, question)

    # Recursively build the true branch.
    true_branch = build_tree(true_rows)

    # Recursively build the false branch.
    false_branch = build_tree(false_rows)

    # Return a Question node.
    # This records the best feature / value to ask at this point,
    # as well as the branches to follow
    # depending on the answer.
    return Decision_Node(question, true_branch, false_branch)


def print_tree(node, spacing=""):
    """World's most elegant tree printing function."""

    # Base case: we've reached a leaf
    if isinstance(node, Leaf):
        print(spacing + "Predict", node.predictions)
        return

    # Print the question at this node
    print(spacing + str(node.question))

    # Call this function recursively on the true branch
    print(spacing + '--> True:')
    print_tree(node.true_branch, spacing + "  ")

    # Call this function recursively on the false branch
    print(spacing + '--> False:')
    print_tree(node.false_branch, spacing + "  ")


def classify(row, node):
    """See the 'rules of recursion' above."""

    # Base case: we've reached a leaf
    if isinstance(node, Leaf):
        return node.predictions

    # Decide whether to follow the true-branch or the false-branch.
    # Compare the feature / value stored in the node,
    # to the example we're considering.
    if node.question.match(row):
        return classify(row, node.true_branch)
    else:
        return classify(row, node.false_branch)


def print_leaf(counts):
    """A nicer way to print the predictions at a leaf."""
    total = sum(counts.values()) * 1.0
    probs = {}
    for lbl in counts.keys():
        probs[lbl] = str(int(counts[lbl] / total * 100)) + "%"
    return probs


if __name__ == '__main__':
    correct = 0
    verbose = False

    training_data, testing_data = split_data(data)
    my_tree = build_tree(training_data)
    if verbose:
        print_tree(my_tree)

    for row in testing_data:
        prediction = classify(row, my_tree)
        guess = list(prediction.keys())[0]

        if verbose:
            print("Actual: %s. Predicted: %s" %
                  (row[-1], print_leaf(prediction)))
        if row[-1] == guess:
            correct += 1
    print("Correct guesses: (%s/%s)" % (correct, len(testing_data)))
    print("Accuracy: %.2f" % (correct * 100 / len(testing_data)))


# Next steps
# - add support for missing (or unseen) attributes
# - prune the tree to prevent overfitting
# - add support for regression
