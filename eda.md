# Common Exploratory Data Analysis (EDA) Techniques

**Exploratory Data Analysis (EDA)** is the process of investigating a dataset before, and sometimes during, machine learning development.

The purpose is not simply to make graphs. The purpose is to **understand what the data contains, discover relationships and patterns, detect problems, and form hypotheses that can later be tested with statistical or machine learning methods.**

The main questions are:

```text
What data do I have?

What does each variable represent?

How are the values distributed?

How are variables related to each other?

How do variables relate to the target?

Are there unusual or problematic observations?

Are there patterns that could help prediction?
```

---

# 1. Dataset Overview

## Purpose

The dataset overview is the first inspection of the data.

Before analyzing relationships or distributions, you need to know **what you are actually working with**.

## Common Checks

```python
df.shape
df.head()
df.info()
df.describe()
```

## What Each One Tells You

### `df.shape`

```python
df.shape
```

Returns:

```text
(rows, columns)
```

For example:

```text
(569, 31)
```

means:

```text
569 samples
31 columns
```

---

### `df.head()`

Shows the first few records.

Useful for understanding:

* What does one row look like?
* What do the columns contain?
* Are values represented as expected?
* Is the target included?

---

### `df.info()`

Shows:

* Column names
* Data types
* Number of non-null values
* Approximate memory usage

This is especially useful for detecting:

```text
Numerical columns
Categorical columns
Missing values
Unexpected data types
```

---

### `df.describe()`

Provides numerical summaries such as:

```text
count
mean
std
min
25%
50%
75%
max
```

This gives you an initial idea of:

```text
Range
Center
Spread
Potential extreme values
```

---

# 2. Target Distribution

## Purpose

Understand the variable you are trying to predict.

For classification:

```python
df["target"].value_counts()
```

Example:

```text
Healthy      357
Malignant    212
```

## Visualization

Usually:

```text
Bar Chart
```

## Questions

* How many samples belong to each class?
* Is the dataset balanced?
* Is one class much smaller than another?
* Could class imbalance affect evaluation?

## Relationship With Other Analyses

Target distribution is important **before feature analysis**.

For example, suppose you later observe:

```text
mean radius
```

has a different distribution for the two classes.

That difference only makes sense when you already know how many samples belong to each class.

So:

```text
Target Distribution
        ↓
provides context for
        ↓
Feature vs Target Analysis
```

---

# 3. Missing Value Analysis

## Purpose

Find incomplete observations.

```python
df.isnull().sum()
```

Example:

```text
mean radius       0
mean texture      0
mean area         5
mean smoothness   0
```

This tells you that `mean area` has five missing values.

## Questions

* Which columns have missing values?
* How many values are missing?
* Are missing values concentrated in particular columns?
* Should they be removed or filled?

## Relationship With EDA

Missing-value analysis affects almost everything else.

For example:

```text
Missing Values
      ↓
Data Quality
      ↓
Distribution Analysis
      ↓
Relationship Analysis
```

You don't want to draw conclusions from a feature without knowing whether a significant portion of its data is missing.

---

# 4. Statistical Summary

## Purpose

Get numerical information about individual variables.

```python
df.describe()
```

For a feature such as:

```text
mean radius
```

you might see:

```text
mean
std
min
25%
50%
75%
max
```

## What This Tells You

### Mean

Typical average value.

### Median

Middle observation.

### Standard Deviation

How spread out the observations are.

### Quartiles

How the data is distributed across four sections.

### Minimum / Maximum

The observed range.

## Relationship With Visualization

Statistical summaries and visualizations complement each other.

For example:

```text
df.describe()
      +
Histogram
      +
Box Plot
```

give you a much better understanding than any one of them alone.

The statistics give you numbers.

The plots let you see the structure behind those numbers.

---

# 5. Histogram

## Purpose

Understand the **distribution of one numerical variable**.

```python
df["mean_radius"].hist(bins=20)
```

A histogram divides values into ranges called **bins** and counts how many observations fall into each range.

## Questions

* What values are common?
* What values are rare?
* Where is the data concentrated?
* How wide is the distribution?
* Is it skewed?
* Are there multiple peaks?
* Are there possible outliers?

## Example

Conceptually:

```text
Frequency
   |
   |          ███
   |        ███████
   |     ███████████
   |  ███████████████
   +--------------------> Value
```

You can see where the observations are concentrated.

## Relationship With Other Analyses

Histogram:

```text
"What does this feature look like?"
```

Correlation:

```text
"Does this feature move with another feature?"
```

Scatter plot:

```text
"What does that relationship actually look like?"
```

So they answer different questions.

---

# 6. Density Plot / KDE

## Purpose

Show the estimated smooth shape of a distribution.

```python
df["mean_radius"].plot(kind="kde")
```

Instead of discrete bars, KDE produces a smooth curve.

## Questions

* Where are the high-density regions?
* Is the distribution unimodal or multimodal?
* Is it skewed?
* Are there multiple groups?

## Relationship With Histogram

They study the **same general concept**:

```text
Distribution
```

but visualize it differently.

```text
Histogram
→ discrete bins

KDE
→ smooth estimated density
```

They can therefore be used together.

---

# 7. Box Plot

## Purpose

Summarize a distribution compactly and identify potential outliers.

A box plot shows:

```text
Minimum / lower range
Q1
Median
Q3
Upper range
Potential outliers
```

## Questions

* Where is the median?
* How spread out is the central portion?
* Are there extreme observations?
* Is the distribution asymmetric?

## Relationship With Histogram

Both examine distribution.

```text
Histogram
→ Shows the overall shape

Box Plot
→ Shows median, quartiles, spread, and outliers compactly
```

For example:

```text
Histogram
    +
Box Plot
```

gives both the **shape** and **statistical summary** of the distribution.

---

# 8. Violin Plot

## Purpose

Compare distributions between groups while also showing their shape.

Example:

```python
sns.violinplot(
    x="target",
    y="mean_radius",
    data=df
)
```

You might see:

```text
Healthy       Malignant

  /\             /\
 /  \           /  \
|    |         |    |
 \  /           \  /
  \/             \/
```

## Questions

* Where are the values concentrated?
* How different are the classes?
* Do their distributions overlap?
* Are there multiple density regions?

## Relationship With Box Plot

A violin plot can be thought of as:

```text
Distribution Shape
        +
Box-plot-like summary
```

So it is especially useful for **feature vs target analysis**.

---

# 9. Correlation Analysis

## Purpose

Measure the degree to which numerical variables move together, usually using a specific correlation coefficient such as Pearson correlation.

For example:

```text
corr(radius, area) = 0.98
```

means they have a very strong positive **linear** association.

## Example

```python
df.corr()
```

## Questions

* Which numerical variables move together?
* Which variables have strong positive relationships?
* Which have strong negative relationships?
* Which variables appear weakly linearly related?
* Which variables may be redundant?

## Example

```text
Radius ↔ Area       = 0.98
Area ↔ Perimeter    = 0.99
```

This suggests that these variables are strongly associated.

You might hypothesize:

> Radius, area, and perimeter are largely describing the same underlying concept: nucleus size.

## Important

Correlation is **not the same as causation**.

And correlation mainly describes a particular form of association, such as linear association for Pearson correlation.

A correlation near zero does not necessarily mean:

```text
"No relationship exists."
```

There may be a nonlinear relationship that Pearson correlation does not capture well.

---

# 10. Correlation Matrix / Heatmap

## Purpose

Look at many pairwise correlations at once.

```python
corr = df.corr()
sns.heatmap(corr)
```

Instead of checking:

```text
radius ↔ area
radius ↔ perimeter
radius ↔ texture
...
```

individually, the matrix displays them together.

## Questions

* Which variables are strongly related?
* Which variables are negatively related?
* Which groups of variables appear redundant?
* Which variables have a strong relationship with the target?

## Relationship With Relationship Analysis

This is where the distinction becomes important:

```text
Relationship Analysis
        ↑
   broad objective
        ↑
Correlation Analysis
        ↑
one statistical method
```

The correlation matrix gives you **evidence** about relationships.

You then investigate those relationships further using plots and domain knowledge.

---

# 11. Scatter Plot

## Purpose

Visually investigate the relationship between two numerical variables.

```python
plt.scatter(
    df["mean_radius"],
    df["mean_area"]
)
```

## Questions

* Is the relationship positive?
* Is it negative?
* Is it approximately linear?
* Is it nonlinear?
* Are there clusters?
* Are there outliers?
* Does the relationship change across different regions?

## Why Use It With Correlation?

Suppose:

```text
corr(radius, area) = 0.98
```

The correlation gives you a numerical summary.

The scatter plot lets you **see why** the correlation is high.

For example:

```text
      •
    •
   •
  •
 •
```

You can visually see the upward relationship.

---

# 12. Pair Plot

## Purpose

Perform many two-variable relationship visualizations simultaneously.

For features:

```text
radius
area
texture
concavity
```

a pair plot can show:

```text
radius ↔ area
radius ↔ texture
radius ↔ concavity
area ↔ texture
area ↔ concavity
texture ↔ concavity
```

and so on.

## Questions

* Which variables appear related?
* Which relationships are nonlinear?
* Are there clusters?
* Are classes visually separable?
* Are there obvious outliers?

## Relationship With Scatter Plot

A pair plot is essentially a **large collection of pairwise visualizations**.

```text
Scatter Plot
→ Investigate one relationship

Pair Plot
→ Investigate many relationships at once
```

---

# 13. Feature vs Target Analysis

## Purpose

Investigate how a feature differs according to the target.

For example:

```text
mean radius
        ↓
Healthy vs Malignant
```

A box plot:

```python
sns.boxplot(
    x="target",
    y="mean_radius",
    data=df
)
```

can show whether the two classes occupy different ranges.

## Questions

* Do the classes have different distributions?
* Is there substantial overlap?
* Does the feature appear useful for classification?
* Are differences consistent or driven by a few observations?

## Relationship With Correlation

This is an important distinction.

You might calculate:

```text
corr(mean_radius, healthy_cells) = -0.73
```

That tells you there is a strong negative linear association.

But a box plot can show you **how the two classes actually differ**.

So:

```text
Correlation
→ Numerical summary of association

Box / Violin Plot
→ Distribution of the feature within each class
```

Together they give more context.

---

# 14. Outlier Analysis

## Purpose

Identify observations that are unusually far from the rest of the data.

## Common Tools

* Box plots
* IQR method
* Z-score
* Histograms
* Scatter plots

## Questions

* Is this observation genuinely unusual?
* Is it a data-entry problem?
* Is it a rare but valid observation?
* Could it represent an important case?

## Relationship With Other Analysis

Outlier analysis is not isolated.

An outlier found in a histogram can be investigated with:

```text
Histogram
    ↓
Possible Outlier
    ↓
Scatter Plot
    ↓
Check Relationships
    ↓
Domain Knowledge
    ↓
Decide whether it is meaningful
```

You should not automatically delete every outlier.

---

# 15. Class Separation Analysis

## Purpose

Investigate whether the classes appear distinguishable based on the available measurements.

For example:

```text
Healthy
Malignant
```

might form visibly different regions in a scatter plot.

## Tools

* Scatter plots
* Pair plots
* Box plots
* Violin plots
* PCA visualization

## Questions

* Do classes occupy different regions?
* How much do they overlap?
* Are there obvious boundaries?
* Which features appear to separate the classes?

## Relationship With Feature vs Target Analysis

These are closely related.

```text
Feature vs Target
→ Study one feature's behavior across classes

Class Separation
→ Study whether the classes can be distinguished using one or more measurements
```

---

# 16. PCA Visualization

## Purpose

PCA (Principal Component Analysis) transforms many numerical variables into a smaller number of new dimensions.

For example:

```text
30 features
      ↓
PCA
      ↓
2 principal components
      ↓
2D visualization
```

Then you can plot:

```text
PC1 vs PC2
```

## Questions

* Does the dataset have large-scale structure?
* Do samples form clusters?
* Do classes appear separated?
* Is much of the variation represented by a few components?

## Important

PCA does **not** simply mean:

> "Choose the two most important original features."

The principal components are combinations of the original variables.

---

# 17. Duplicate Analysis

## Purpose

Find repeated observations.

```python
df.duplicated().sum()
```

## Questions

* Are there duplicate records?
* Could repeated samples cause problems?
* Could the same observation appear in both training and testing data?

## Why It Matters

Suppose the exact same sample appears in:

```text
Training Set
+
Testing Set
```

The model may appear to perform extremely well because it has effectively already seen the test observation.

So duplicate analysis is also related to **data leakage prevention**.

---

# 18. Feature Importance Analysis

## Purpose

After training a model, investigate which variables the model relied on according to the particular importance method being used.

Example:

```python
model.feature_importances_
```

## Questions

* Which features contributed strongly according to this model/method?
* Which features contributed less?
* Does the model's behavior resemble what EDA suggested?

## Important Distinction

This is different from ordinary EDA because it usually happens **after a model exists**.

Earlier:

```text
EDA
↓
"What does the data appear to say?"
```

Later:

```text
Model
↓
"What did this trained model use?"
```

You can then compare the two.

For example:

```text
EDA:
Worst concave points appears strongly related to diagnosis.

Model:
Worst concave points receives substantial importance.
```

That provides a useful consistency check, although feature importance should not automatically be interpreted as causation.

---

# How These Analyses Connect

This is the most important part.

EDA is not a collection of unrelated graphs.

You can think of it as a chain of questions.

```text
                    DATASET
                       |
                       v
              Dataset Overview
                       |
          +------------+------------+
          |                         |
          v                         v
     Data Quality              Target
          |                         |
          v                         v
 Missing Values               Class Balance
 Duplicates                       |
          |                         |
          +------------+------------+
                       |
                       v
              Individual Features
                       |
             +---------+---------+
             |                   |
             v                   v
        Distribution       Statistics
             |                   |
       +-----+-----+             |
       |           |             |
       v           v             |
 Histogram       Box Plot        |
       |           |             |
       +-----+-----+-------------+
             |
             v
       Feature Relationships
             |
       +-----+-----+
       |           |
       v           v
 Correlation   Scatter Plot
       |           |
       +-----+-----+
             |
             v
       Relationship Analysis
             |
             v
      Feature ↔ Target
             |
       +-----+-----+
       |           |
       v           v
   Box/Violin   Scatter/Pairs
       |           |
       +-----+-----+
             |
             v
       Class Separation
             |
             v
        Model Training
             |
             v
      Feature Importance
             |
             v
      Compare Model
      With EDA Findings
```

---

# A Concrete Example From Your Breast Cancer Dataset

Suppose you start with:

```text
mean radius
mean area
mean perimeter
```

### Step 1 — Distribution

Histogram:

```text
mean radius
```

You discover:

> Most observations are concentrated around a particular range, with some larger values.

---

### Step 2 — Correlation

You calculate:

```text
corr(radius, area) ≈ 0.98
```

You now have evidence that they move together strongly.

---

### Step 3 — Scatter Plot

You plot:

```text
radius vs area
```

and see a strong upward pattern.

Now the numerical correlation has a visual explanation.

---

### Step 4 — Domain Interpretation

You know:

```text
Radius → size
Area   → size
```

Therefore:

> Radius and area are strongly related because both largely describe nucleus size.

This is **relationship analysis**.

Notice how several techniques contributed:

```text
Correlation
      +
Scatter Plot
      +
Domain Knowledge
      ↓
Relationship Interpretation
```

---

# Another Example: Feature vs Target

Suppose you find:

```text
corr(worst_concave_points, healthy_cells)
= -0.79
```

You now investigate further.

### Histogram

Shows the overall distribution.

```text
What values are common?
```

### Box Plot

Compare:

```text
Healthy
vs
Malignant
```

### Violin Plot

Look at the full distribution for each class.

### Scatter Plot

Compare it with another related feature.

For example:

```text
worst concave points
        vs
worst radius
```

Now you can form a stronger conclusion about the role of boundary irregularity.

---

# The Difference Between "Analysis" and "Tools"

This distinction is worth remembering.

## Analysis = The Question / Goal

Examples:

```text
Distribution Analysis
Relationship Analysis
Outlier Analysis
Class Separation Analysis
Feature Importance Analysis
```

## Tools = How You Investigate It

Examples:

```text
Histogram
KDE
Correlation
Scatter Plot
Box Plot
Violin Plot
PCA
Statistical Tests
```

One analysis can use several tools.

One tool can also contribute to several analyses.

For example:

```text
                    Scatter Plot
                   /      |       \
                  /       |        \
                 v        v         v
          Relationship  Outlier   Class
            Analysis    Analysis  Separation
```

So there is **not a strict one-to-one relationship** between an analysis and a visualization.

---

# A Better Mental Model

Instead of memorizing:

```text
Histogram = EDA
Correlation = EDA
Scatter = EDA
```

think:

```text
                 EDA
                  |
        "What is happening in my data?"
                  |
       +----------+----------+
       |          |          |
       v          v          v
 Distribution  Relationships  Quality
       |          |          |
       v          v          v
 Histogram    Correlation   Missing Values
 KDE          Scatter       Duplicates
 Box Plot     Pair Plot     Outliers
              Box Plot
                  |
                  v
             Target Analysis
                  |
                  v
            Class Separation
                  |
                  v
             Model Building
                  |
                  v
          Model Interpretation
```

This is much closer to how you should think about EDA.

---

# Typical Classification EDA Workflow

There is no mandatory order, but a sensible workflow is:

```text
1. Understand the dataset
        ↓
2. Understand the target
        ↓
3. Check data quality
        ↓
4. Understand individual feature distributions
        ↓
5. Investigate feature-to-feature relationships
        ↓
6. Investigate feature-to-target relationships
        ↓
7. Investigate class separation
        ↓
8. Investigate outliers and unusual observations
        ↓
9. Form hypotheses
        ↓
10. Train a baseline model
        ↓
11. Interpret the model
        ↓
12. Compare model findings with EDA findings
```

The important part is that **EDA is iterative**.

You might discover something in a correlation matrix that makes you go back to a scatter plot.

You might see an unusual cluster in a scatter plot and go back to the raw records.

You might see class separation in a box plot and then test whether a classifier actually benefits from that feature.

So EDA is less like:

```text
Do 17 plots → Done
```

and more like:

```text
Observe
   ↓
Ask a question
   ↓
Investigate
   ↓
Form a hypothesis
   ↓
Check it using another view of the data
   ↓
Interpret
   ↓
Ask the next question
```

That is the mindset you want to develop while working through the Breast Cancer dataset.
