# pylint: disable=missing-docstring, broad-except, unused-import
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
import time
import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime

# Fail fast if these aren't installed - standard dev behavior
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

class UniScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.session = requests.Session()
        # Spoof user agent to avoid basic bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.df = None

    def fetch(self, url):
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return BeautifulSoup(resp.content, 'html.parser')
        except Exception as e:
            print(f"[!] Failed to fetch {url}: {e}")
            return None

    def get_course_links(self, soup):
        # Filtering for master's/postgrad keywords
        keywords = ['msc', 'master', 'postgraduate', 'degree', 'study']
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            txt = a.get_text().lower()
            if any(k in txt or k in href.lower() for k in keywords):
                full = urljoin(self.base_url, href)
                if self.domain in full:
                    links.add(full)
        
        # Cap at 15 pages to prevent rate-limiting during testing
        return list(links)[:15]

    def parse_fee(self, text):
        # Extract numeric value from strings like "£12,500 per year"
        if not text: return None
        clean = re.sub(r'[^\d.]', '', text.split('per')[0]) # Simple split to avoid duration numbers
        try:
            return float(clean)
        except:
            return None

    def scrape(self):
        print(f"--> Target: {self.base_url}")
        soup = self.fetch(self.base_url)
        if not soup: return

        links = self.get_course_links(soup)
        print(f"--> Found {len(links)} potential course pages. Starting crawl...")

        data = []
        for i, link in enumerate(links):
            print(f"    [{i+1}/{len(links)}] Parsing {link}...")
            page = self.fetch(link)
            if not page: continue

            # Naive extraction - assumes course title is H1
            h1 = page.find('h1')
            title = h1.get_text().strip() if h1 else "Unknown"
            
            # Grab all text to search for fees
            body_text = page.get_text(" ", strip=True)
            
            # Regex for currency (GBP/USD/EUR)
            fee_match = re.search(r'[£$€]\s?[\d,]+', body_text)
            raw_fee = fee_match.group(0) if fee_match else None
            
            data.append({
                'title': title,
                'url': link,
                'raw_fee': raw_fee,
                'fee_val': self.parse_fee(raw_fee)
            })
            time.sleep(1) # Be nice to the server

        self.df = pd.DataFrame(data)
        # Drop courses where we couldn't find a fee
        self.df = self.df.dropna(subset=['fee_val'])
        print(f"--> Done. Extracted {len(self.df)} valid courses.")
        return self.df

    def analyze(self):
        if self.df is None or self.df.empty:
            print("No data to analyze.")
            return

        # 1. Cluster courses (TF-IDF + K-Means)
        # This groups courses by topic (e.g., "AI", "Business", "Health")
        vec = TfidfVectorizer(stop_words='english')
        X = vec.fit_transform(self.df['title'])
        model = KMeans(n_clusters=min(3, len(self.df)), n_init=10)
        self.df['cluster'] = model.fit_predict(X)

        # 2. Save to DB
        conn = sqlite3.connect('universities.db')
        self.df.to_sql('courses', conn, if_exists='replace', index=False)
        print("--> Saved to universities.db")

        # 3. Visualization
        if not os.path.exists('analysis'): os.makedirs('analysis')
        
        plt.figure(figsize=(10,6))
        sns.boxplot(data=self.df, x='cluster', y='fee_val')
        plt.title('Tuition Fee Ranges by Course Cluster')
        plt.ylabel('Fee')
        plt.savefig('analysis/fee_clusters.png')
        print("--> Chart saved to analysis/fee_clusters.png")

if __name__ == "__main__":
    # Default to Imperial's PG page if no input
    target = input("Enter URL (default: Imperial PG): ") or "https://www.imperial.ac.uk/study/pg/"
    
    app = UniScraper(target)
    app.scrape()
    app.analyze()