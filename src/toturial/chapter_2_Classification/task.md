# Project 1: Binary Classification

## Project Name
**Cell Mass Diagnostic Classifier**

## Dataset
Breast Cancer Wisconsin (Diagnostic) Dataset

```python
from sklearn.datasets import load_breast_cancer
```

## Definition

The Breast Cancer Wisconsin (Diagnostic) Dataset is a medical dataset commonly used for evaluating binary classification algorithms. It contains measurements computed from digitized images of fine needle aspirate (FNA) samples taken from breast masses. These measurements describe characteristics of cell nuclei such as radius, texture, perimeter, area, smoothness, and other morphological properties.

The objective of the dataset is to determine whether a detected breast mass is:

- **Benign (non-cancerous)**
- **Malignant (cancerous)**

This project implements a supervised binary classification pipeline that learns relationships between 30 continuous numerical features and the diagnostic outcome. The dataset is selected because it is a well-structured real-world medical classification problem that introduces important concepts such as feature scaling, decision thresholds, false positives, false negatives, and evaluation metrics beyond simple accuracy.

## Scope & Verification Goals

- Test how raw vs. standardized feature scales impact model decision boundaries.
- Adjust decision probability thresholds to prioritize reducing False Negatives over False Positives.
- Evaluate precision, recall, F1-score, and ROC-AUC against simple accuracy.

---

# Project 2: Multi-Class Classification

## Project Name
**Specimen Morphological Classifier**

## Dataset

### Option 1: Iris Flower Dataset

```python
from sklearn.datasets import load_iris
```

### Option 2: Wine Recognition Dataset

```python
from sklearn.datasets import load_wine
```

## Definition

The Iris Dataset is one of the most widely used introductory machine learning datasets. It contains physical measurements of iris flowers, including sepal length, sepal width, petal length, and petal width. The goal is to classify each flower into one of three species:

- Iris Setosa
- Iris Versicolor
- Iris Virginica

Alternatively, the Wine Recognition Dataset contains chemical analysis measurements from wines produced in different cultivars. The task is to classify a wine sample into one of three wine categories based on its chemical properties.

This project focuses on multi-class classification, where each sample belongs to exactly one class among several possible classes. These datasets are chosen because they provide clearly labeled categories and allow visualization of class boundaries, making them ideal for studying how machine learning models separate multiple classes within feature space.

## Scope & Verification Goals

- Analyze how linear and non-linear classifiers partition feature space into multiple decision regions.
- Compare One-vs-Rest (OvR) strategies against native multi-class decision boundaries.
- Identify overlapping class boundary zones and observe how model confidence decreases near intersection points.

---

# Project 3: Multi-Output / Multi-Label Classification

## Project Name
**Multi-Attribute Signal Tagging Engine**

## Dataset

### Option 1: Synthetic Multi-Label Dataset

```python
from sklearn.datasets import make_multilabel_classification
```

### Option 2: Yeast Gene Function Dataset

UCI Machine Learning Repository

## Definition

Traditional classification problems assume that each sample belongs to exactly one class. However, many real-world problems require predicting multiple labels simultaneously.

For example:

- A news article may belong to "Politics", "Economy", and "International" categories at the same time.
- An image may contain a "Car", "Person", and "Road" simultaneously.
- A gene may perform multiple biological functions.

The Synthetic Multi-Label Dataset generates artificial samples with multiple target labels, making it useful for understanding the mathematical foundations of multi-label learning. The Yeast Dataset is a real-world biological dataset where genes may be associated with several functional categories simultaneously.

This project implements a multi-output classification system where each sample predicts a binary target matrix:

\[
Y \in \{0,1\}^{N \times K}
\]

instead of a single target variable: \[y\]

where:

- \(N\) = Number of samples
- \(K\) = Number of labels

The project is designed to explore how machine learning models handle multiple outputs and how evaluation differs from traditional classification tasks.

## Scope & Verification Goals

- Implement predictions for a 2D binary target matrix where target variables are independent or correlated.
- Compare problem transformation approaches (training multiple binary classifiers) against native multi-output classifiers.
- Evaluate performance using multi-label specific metrics such as:
  - Hamming Loss
  - Exact Match Ratio (Subset Accuracy)
  - Jaccard Score