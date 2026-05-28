import csv
import os
from collections import defaultdict
from pathlib import Path

def load_csv(filepath: str) -> dict:
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
    
    # Summary table - which files contain each article
    print("\n" + "="*80)
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
    
    with open('results/article_comparison_report.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['PMID', 'Title', 'Year', 'Files'] + file_names
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pmid in sorted(all_pmids, key=lambda x: int(x)):
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

if __name__ == '__main__':
    # Create results directory if it doesn't exist
    Path('results').mkdir(exist_ok=True)
    
    compare_articles()
