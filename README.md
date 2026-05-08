# Komoot-based Trail Recommender System

Final project for **Machine Learning Applications**  
Bachelor in Data Science and Engineering — UC3M  

**Group 14**
- Raquel Jaén Delgado
- Jorge Barcia Belinchón
- Sergio Madrid Cuevas
- Enica King Chiong

---

## Project Overview

This project develops a **trail recommender system** using data scraped from **Komoot**, an outdoor route-planning platform.

The selected task is:

**Task 2.3 — Recommendation Systems**

Each trail is treated as an item. The goal is to recommend similar trails using their textual descriptions and available metadata.

---

## Repository Structure

```text
ml-applications-project-repo/
│
├── data/
│   ├── raw/              # Raw JSON files scraped from Komoot
│   └── trails.pkl        # Processed dataset
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_task1_nlp.ipynb
│   ├── 03_task2_recommender.ipynb
│   └── 04_report_figures.ipynb
│
├── report/
│   ├── figures/
│   └── tables/
│
├── scrape_batch.py
├── requirements.txt
└── README.md
```

---

## Dataset

The dataset was created through web scraping from Komoot because no suitable public dataset was found.

Initial dataset:

- **10,902 trails**
- **45 columns**

For the NLP task, only trails with a valid `description` were kept.

Final working dataset:

- **5,642 trails with descriptions**

Relevant fields include:

- `tour_id`
- `name`
- `sport`
- `difficulty`
- `distance_m`
- `duration_s`
- `elevation_up_m`
- `elevation_down_m`
- `region`
- `description`
- `rating_score`
- `rating_count`
- `visitors`

Since the data was scraped, some fields contain missing values or nested structures.

---

## Notebooks

### `01_data_exploration.ipynb`

Loads the raw JSON files, explores the dataset, filters trails without descriptions, and creates the processed dataset:

```text
data/trails.pkl
```

### `02_task1_nlp.ipynb`

Performs text preprocessing and vectorization.

Preprocessing steps:

- Lowercasing
- Tokenization
- Stopword removal
- Punctuation removal
- Lemmatization with SpaCy
- Removal of short tokens

Vectorization methods:

| Type | Method | Dimension |
|---|---:|---:|
| Classical | TF-IDF | 5000 |
| Embedding-based | FastText | 100 |
| Topic modeling | LDA | 20 |
| Contextual embeddings | BERT / SentenceTransformer | 384 |

### `03_task2_recommender.ipynb`

Implements the recommender system.

Current confirmed implementation:

- Content-based recommendation
- Cosine similarity between trail vectors
- Evaluation with `Sport Precision@10`

Results:

| Representation | Sport Precision@10 |
|---|---:|
| TF-IDF | 0.217 |
| FastText | 0.216 |
| LDA | 0.210 |
| BERT / SentenceTransformer | 0.219 |

Collaborative filtering is still under development.

### `04_report_figures.ipynb`

Generates figures and tables for the final report, such as:

- Sport distribution
- Difficulty distribution
- Rating distribution
- Distance distribution
- Dataset summary tables

Outputs are saved in:

```text
report/figures/
report/tables/
```

---


## Current Status

| Component | Status |
|---|---|
| Dataset creation | Completed |
| Data exploration | Completed |
| Text preprocessing | Completed |
| Text vectorization | Completed |
| Content-based recommender | Completed |
| Collaborative filtering | In progress |
| Hybrid recommender | Not finalized |
| Final report | In progress |
| Presentation | In progress |

---

## Known Limitations

- Some trails have missing ratings.
- The dataset does not contain a complete real user-item interaction matrix.
- `Sport Precision@10` is only an indirect evaluation metric.
- Some scraped fields are missing, nested, or inconsistent.

---

## External Libraries

Main libraries used:

- pandas
- NumPy
- scikit-learn
- SpaCy
- Gensim
- SentenceTransformers
- Surprise

External sources or code snippets used in the final project should be acknowledged in the report.
