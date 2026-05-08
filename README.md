# Komoot-based Trail Recommender System

Final project for the **Machine Learning Applications** course  
Bachelor in Data Science and Engineering — UC3M  

**Group 14**

- Raquel Jaén Delgado
- Jorge Barcia Belinchón
- Sergio Madrid Cuevas
- Enica King Chiong

---

## 1. Project Overview

This project develops a **trail recommender system** based on data scraped from [Komoot](https://www.komoot.com/), an outdoor activity and route-planning platform.

The goal is to recommend trails in Spain using textual route descriptions and available trail metadata. The project follows the requirements of the Machine Learning Applications final assignment, focusing on:

1. Dataset creation through web scraping.
2. Natural Language Processing and text vectorization.
3. Implementation of a recommender system.

The selected machine learning task is:

> **Task 2.3: Recommendation Systems**

Each trail is treated as an item, and the system recommends similar trails based on textual similarity and available metadata.

---

## 2. Repository Structure

```text
ml-applications-project-repo/
│
├── data/
│   ├── raw/
│   │   └── Raw JSON files scraped from Komoot
│   │
│   └── trails.pkl
│       Processed dataset used by the notebooks
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_task1_nlp.ipynb
│   ├── 03_task2_recommender.ipynb
│   └── 04_report_figures.ipynb
│
├── report/
│   ├── figures/
│   │   └── Generated figures for the final report
│   │
│   └── tables/
│       └── Generated tables for the final report
│
├── scrape_batch.py
│
├── requirements.txt
│
└── README.md
