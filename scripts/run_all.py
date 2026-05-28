#!/usr/bin/env python3
"""
All-in-one PubMed Article Fetcher and Comparison Tool
Fetches article data from PubMed and compares overlaps across multiple files
"""

import requests
import csv
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# ============================================================================
# PART 1: FETCH PUBMED ARTICLES
# ============================================================================

def fetch_pubmed_articles(pmids: List[int], output_file: str = 'data/MoCD_cPMP_combined_articles.csv') -> Dict[str, dict]:
    """
    Fetch article details from PubMed API using PMID list
    Returns dictionary of articles and saves to CSV
    """
    
    # Remove duplicates and sort
    pmids = list(set(pmids))
    pmids.sort()
    
    print("="*80)
    print("STEP 1: FETCHING PUBMED ARTICLES")
    print("="*80)
    print(f"Fetching data for {len(pmids)} unique PMIDs...\n")
    
    articles = []
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    # Batch requests (100 IDs per request)
    batch_size = 100
    for batch_num, i in enumerate(range(0, len(pmids), batch_size)):
        batch = pmids[i:i+batch_size]
        batch_str = ','.join([str(pmid) for pmid in batch])
        
        print(f"Batch {batch_num + 1}/{(len(pmids) + batch_size - 1) // batch_size}...", end=" ", flush=True)
        
        try:
            params = {
                "db": "pubmed",
                "id": batch_str,
                "retmode": "json"
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            
            if 'result' in data:
                for pmid in batch:
                    pmid_str = str(pmid)
                    if pmid_str in data['result']:
                        article = data['result'][pmid_str]
                        
                        # Extract relevant fields
                        title = article.get('title', 'N/A')
                        authors_list = article.get('authors', [])
                        authors = ', '.join([a.get('name', '') for a in authors_list]) if authors_list else 'N/A'
                        journal = article.get('source', 'N/A')
                        pubdate = article.get('pubdate', 'N/A')
                        year = pubdate.split()[-1] if pubdate and pubdate != 'N/A' else 'N/A'
                        doi = article.get('doi', 'N/A')
                        
                        articles.append({
                            'PMID': pmid,
                            'Title': title,
                            'Authors': authors,
                            'Journal': journal,
                            'Year': year,
                            'DOI': doi,
                            'Notes': ''
                        })
            
            print("✓")
            # Be respectful to NCBI servers
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # Write to CSV
    if articles:
        # Create data directory if it doesn't exist
        Path('data').mkdir(exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['PMID', 'Title', 'Authors', 'Journal', 'Year', 'DOI', 'Notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)
        
        print(f"\n✓ Successfully fetched and saved {len(articles)} articles")
        print(f"✓ Output saved to: {output_file}\n")
        return {article['PMID']: article for article in articles}
    else:
        print("✗ No articles were fetched.\n")
        return {}

# ============================================================================
# PART 2: COMPARE ARTICLES
# ============================================================================

def load_csv(filepath: str) -> Dict[str, dict]:
    """Load CSV file and return dict with PMID as key"""
    articles = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pmid = row.get('PMID', '').strip()
                if pmid:
                    articles[pmid] = row
        return articles
    except FileNotFoundError:
        print(f"Warning: File {filepath} not found")
        return {}

def compare_articles(data_dir: str = 'data') -> None:
    """Compare article overlap across all CSV files in data directory"""
    
    print("="*80)
    print("STEP 2: COMPARING ARTICLES ACROSS FILES")
    print("="*80 + "\n")
    
    # Find all CSV files
    csv_files = list(Path(data_dir).glob('*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}/")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to compare:\n")
    
    # Load all files
    file_data = {}
    for csv_file in sorted(csv_files):
        file_data[csv_file.stem] = load_csv(str(csv_file))
        print(f"  • {csv_file.name}: {len(file_data[csv_file.stem])} articles")
    
    print("\n" + "="*80)
    print("OVERLAP ANALYSIS")
    print("="*80 + "\n")
    
    # Get all unique PMIDs
    all_pmids = set()
    for articles in file_data.values():
        all_pmids.update(articles.keys())
    
    print(f"Total unique articles across all files: {len(all_pmids)}\n")
    
    # Pairwise comparison
    file_names = sorted(file_data.keys())
    if len(file_names) > 1:
        for i, file1 in enumerate(file_names):
            for file2 in file_names[i+1:]:
                pmids1 = set(file_data[file1].keys())
                pmids2 = set(file_data[file2].keys())
                
                overlap = pmids1 & pmids2
                unique_to_1 = pmids1 - pmids2
                unique_to_2 = pmids2 - pmids1
                
                print(f"{file1} vs {file2}:")
                print(f"  • Overlapping articles: {len(overlap)}")
                print(f"  • Unique to {file1}: {len(unique_to_1)}")
                print(f"  • Unique to {file2}: {len(unique_to_2)}")
                print()
    else:
        print("Only one file found - no comparison possible\n")
    
    # Summary table - which files contain each article
    print("="*80)
    print("ARTICLE PRESENCE MATRIX")
    print("="*80 + "\n")
    
    # Create presence matrix
    presence = defaultdict(list)
    for filename, articles in file_data.items():
        for pmid in articles.keys():
            presence[pmid].append(filename)
    
    # Group by number of files
    by_count = defaultdict(list)
    for pmid, files in presence.items():
        by_count[len(files)].append((pmid, files))
    
    # Print summary
    for count in sorted(by_count.keys(), reverse=True):
        pmids_list = by_count[count]
        print(f"In {count} file(s) ({len(pmids_list)} articles):")
        for pmid, files in sorted(pmids_list)[:5]:  # Show first 5
            print(f"  • PMID {pmid}: {', '.join(files)}")
        if len(pmids_list) > 5:
            print(f"  ... and {len(pmids_list) - 5} more")
        print()
    
    # Export detailed comparison
    print("="*80)
    print("GENERATING DETAILED COMPARISON REPORT")
    print("="*80 + "\n")
    
    Path('results').mkdir(exist_ok=True)
    
    with open('results/article_comparison_report.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['PMID', 'Title', 'Year', 'Files'] + file_names
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pmid in sorted(all_pmids, key=lambda x: int(x) if x.isdigit() else 0):
            row = {'PMID': pmid, 'Files': ''}
            files_with_pmid = []
            
            # Get article info and check presence
            for filename in file_names:
                if pmid in file_data[filename]:
                    article = file_data[filename][pmid]
                    row['Title'] = article.get('Title', '')
                    row['Year'] = article.get('Year', '')
                    row[filename] = '✓'
                    files_with_pmid.append(filename)
                else:
                    row[filename] = ''
            
            row['Files'] = '; '.join(files_with_pmid)
            writer.writerow(row)
    
    print(f"✓ Detailed report saved to: results/article_comparison_report.csv\n")
    print("="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # List of PMIDs to fetch
    pmids = [
        35192225, 34870926, 36296488, 20385644, 30108670, 34012852, 33488670, 34013236,
        34403026, 33897766, 30900395, 32099439, 33502714, 25709896, 35692435, 33840416,
        33446569, 33552910, 19907877, 32802950, 23430915, 29106383, 37789894, 38463082,
        38187804, 25764214, 29696052, 32014857, 12385777, 10903949, 29899766, 37836841,
        27289259, 36423681, 20573177, 23203137, 30619713, 12732628, 33526584, 17236133,
        28524215, 37817707, 26575208
    ]
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "PubMed Article Fetcher & Comparison Tool".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Step 1: Fetch articles
    fetch_pubmed_articles(pmids)
    
    # Step 2: Compare articles
    compare_articles()
    
    print("All done! Check the 'data/' and 'results/' directories for output files.\n")
