import requests
import csv
from io import StringIO
import time

# List of PMIDs to fetch
pmids = [
    35192225, 34870926, 36296488, 20385644, 30108670, 34012852, 33488670, 34013236,
    34403026, 33897766, 30900395, 32099439, 33502714, 25709896, 35692435, 33840416,
    33446569, 33552910, 19907877, 32802950, 23430915, 29106383, 37789894, 38463082,
    38187804, 25764214, 29696052, 32014857, 12385777, 10903949, 29899766, 37836841,
    27289259, 36423681, 20573177, 23203137, 30619713, 12732628, 33526584, 17236133,
    28524215, 37817707, 26575208
]

# Remove duplicates
pmids = list(set(pmids))

articles = []

# Fetch article details from PubMed
for pmid in pmids:
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        response = requests.get(url)
        data = response.json()
        
        if 'result' in data and str(pmid) in data['result']:
            article = data['result'][str(pmid)]
            
            # Extract relevant fields
            title = article.get('title', 'N/A')
            authors_list = article.get('authors', [])
            authors = ', '.join([f"{a.get('name', '')}" for a in authors_list]) if authors_list else 'N/A'
            journal = article.get('source', 'N/A')
            year = article.get('pubdate', 'N/A').split()[0] if article.get('pubdate') else 'N/A'
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
            
            print(f"✓ Fetched PMID {pmid}")
        else:
            print(f"✗ Could not find PMID {pmid}")
            
        # Be respectful to NCBI servers - add delay
        time.sleep(0.5)
        
    except Exception as e:
        print(f"✗ Error fetching PMID {pmid}: {str(e)}")

# Write to CSV
csv_output = StringIO()
if articles:
    fieldnames = ['PMID', 'Title', 'Authors', 'Journal', 'Year', 'DOI', 'Notes']
    writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(articles)
    
    print(f"\n✓ Successfully fetched {len(articles)} articles")
    print("\nCSV Output:")
    print(csv_output.getvalue())
else:
    print("No articles were fetched.")
