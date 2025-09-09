from datetime import datetime
from urllib.parse import urlparse

def generate_case_citation(case_name, volume, reporter, page, court, year):
    """Generate a case law citation in standard format."""
    if all([case_name, volume, reporter, page, year]):
        return f"{case_name}, {volume} {reporter} {page} ({court} {year})"
    return None

def generate_website_citation(author, title, website, access_date, url):
    """Generate a website citation in MLA/APA/Bluebook style."""
    if title and website and url:
        # MLA Style
        author_part = f"{author}, " if author else ""
        access_date_str = access_date.strftime("%d %b %Y") if access_date else datetime.now().strftime("%d %b %Y")
        return f'{author_part}"{title}," {website}, Accessed: {access_date_str}, {url}'
    return None

def extract_citation_info_from_url(url):
    """Attempt to extract citation information from URL."""
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.lower()
    
    # Identify legal databases and courts
    legal_sources = {
        'supremecourt.gov': ('Supreme Court', 'U.S.'),
        'ca.gov': ('Court of Appeals', 'U.S.'),
        'state.nj.us': ('Superior Court', 'New Jersey'),
        'indianjudiciary.gov': ('Supreme Court', 'India'),
        'judiciary.uk': ('High Court', 'UK'),
        'austlii.edu.au': ('Federal Court', 'Australia'),
        'canlii.org': ('Supreme Court', 'Canada')
    }
    
    for domain, info in legal_sources.items():
        if domain in netloc:
            return info  # (court, jurisdiction)
    
    return (None, None)

def generate_citation(result):
    """Generate citation based on search result metadata."""
    # Case Law Citation
    if all(key in result for key in ['case_name', 'volume', 'reporter', 'page', 'court', 'year']):
        return generate_case_citation(
            result['case_name'],
            result['volume'],
            result['reporter'],
            result['page'],
            result['court'],
            result['year']
        )
    
    # Website Citation
    court, jurisdiction = extract_citation_info_from_url(result.get('link', ''))
    
    return generate_website_citation(
        author=result.get('author', result.get('publisher', None)),
        title=result.get('title', 'Unknown Title'),
        website=result.get('publisher', court or jurisdiction or 'Unknown Source'),
        access_date=datetime.now(),
        url=result.get('link', result.get('url', ''))
    )

def format_search_results_with_citations(results):
    """Add citations to search results payload."""
    for result in results:
        result['citation'] = generate_citation(result)
    
    return results