# University Tuition Data Pipeline

A Python-based data extraction and analysis pipeline designed to aggregate UK university course fees and identify pricing trends using K-Means clustering.

I built this to automate the collection of tuition data, which is often unstructured and inconsistent across university websites.

## 🛠️ Tech Stack
- **Core:** Python 3.9+
- **Scraping:** Requests, BeautifulSoup4 (with custom User-Agent rotation)
- **Data Processing:** Pandas, NumPy, Regex (for currency cleaning)
- **Storage:** SQLite3 (`universities.db`)
- **Analysis:** Scikit-Learn (K-Means), Matplotlib, Seaborn

## 📂 Project Structure
```text
├── uni_scraper.py           # Main extraction logic (Scraper -> SQLite)
├── analysis_notebook.ipynb  # Jupyter notebook for EDA and visualizations
├── analysis/                # Generated charts (Fee distributions, clusters)
├── courses.json             # Sample raw output
└── requirements.txt         # Dependencies