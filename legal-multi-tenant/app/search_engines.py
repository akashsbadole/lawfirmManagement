"""
External search engine integrations for legal research
"""
import requests
import json
from urllib.parse import quote_plus
from app import app
from datetime import datetime
import time

class SearchEngineError(Exception):
    """Custom exception for search engine errors"""
    pass

class GoogleSearchEngine:
    """Google Custom Search API integration"""
    
    def __init__(self):
        self.api_key = app.config.get('GOOGLE_SEARCH_API_KEY')
        self.cx = app.config.get('GOOGLE_SEARCH_CX')
        self.base_url = 'https://www.googleapis.com/customsearch/v1'
    
    def search(self, query, num_results=10, site_restrict=None):
        """
        Search using Google Custom Search API
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return (max 10 per request)
            site_restrict (str): Restrict search to specific site (e.g., 'justia.com')
        
        Returns:
            dict: Search results
        """
        if not self.api_key or not self.cx:
            raise SearchEngineError("Google Search API credentials not configured")
        
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': min(num_results, 10)
        }
        
        if site_restrict:
            params['siteSearch'] = site_restrict
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', ''),
                    'formattedUrl': item.get('formattedUrl', ''),
                    'source': 'Google'
                })
            
            return {
                'results': results,
                'total_results': data.get('searchInformation', {}).get('totalResults', 0),
                'search_time': data.get('searchInformation', {}).get('searchTime', 0)
            }
            
        except requests.exceptions.RequestException as e:
            raise SearchEngineError(f"Google Search API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise SearchEngineError(f"Invalid JSON response from Google Search API: {str(e)}")

class BingSearchEngine:
    """Bing Web Search API integration"""
    
    def __init__(self):
        self.api_key = app.config.get('BING_SEARCH_API_KEY')
        self.base_url = 'https://api.bing.microsoft.com/v7.0/search'
    
    def search(self, query, num_results=10, site_restrict=None):
        """
        Search using Bing Web Search API
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            site_restrict (str): Restrict search to specific site
        
        Returns:
            dict: Search results
        """
        if not self.api_key:
            raise SearchEngineError("Bing Search API key not configured")
        
        search_query = query
        if site_restrict:
            search_query = f"site:{site_restrict} {query}"
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key
        }
        
        params = {
            'q': search_query,
            'count': min(num_results, 50),
            'responseFilter': 'Webpages'
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get('webPages', {}).get('value', []):
                results.append({
                    'title': item.get('name', ''),
                    'link': item.get('url', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayUrl', ''),
                    'source': 'Bing'
                })
            
            return {
                'results': results,
                'total_results': data.get('webPages', {}).get('totalEstimatedMatches', 0)
            }
            
        except requests.exceptions.RequestException as e:
            raise SearchEngineError(f"Bing Search API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise SearchEngineError(f"Invalid JSON response from Bing Search API: {str(e)}")

class DuckDuckGoSearchEngine:
    """DuckDuckGo search integration (no API key required)"""
    
    def __init__(self):
        self.base_url = 'https://api.duckduckgo.com/'
    
    def search(self, query, num_results=10, site_restrict=None):
        """
        Search using DuckDuckGo Instant Answer API
        Note: This API has limitations and may not return web results
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return (ignored for DDG)
            site_restrict (str): Site restriction (ignored for DDG)
        
        Returns:
            dict: Search results
        """
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Add abstract if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', query),
                    'link': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', ''),
                    'displayLink': data.get('AbstractSource', ''),
                    'source': 'DuckDuckGo'
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'link': topic.get('FirstURL', ''),
                        'snippet': topic.get('Text', ''),
                        'displayLink': 'duckduckgo.com',
                        'source': 'DuckDuckGo'
                    })
            
            return {
                'results': results,
                'total_results': len(results)
            }
            
        except requests.exceptions.RequestException as e:
            raise SearchEngineError(f"DuckDuckGo Search error: {str(e)}")
        except json.JSONDecodeError as e:
            raise SearchEngineError(f"Invalid JSON response from DuckDuckGo: {str(e)}")

class LegalSearchAggregator:
    """Aggregates results from multiple search engines with legal site focus"""
    
    def __init__(self):
        self.google = GoogleSearchEngine()
        self.bing = BingSearchEngine()
        self.duckduckgo = DuckDuckGoSearchEngine()
        
        # Legal websites to prioritize
        self.legal_sites = [
            'justia.com',
            'findlaw.com',
            'law.cornell.edu',
            'caselaw.findlaw.com',
            'scholar.google.com',
            'courtlistener.com',
            'law.com',
            'martindale.com',
            'avvo.com'
        ]
    
    def search_legal_sites(self, query, engine='google', num_results=10):
        """
        Search specifically within legal websites
        
        Args:
            query (str): Search query
            engine (str): Search engine to use ('google', 'bing', 'duckduckgo')
            num_results (int): Number of results per site
        
        Returns:
            dict: Aggregated search results
        """
        all_results = []
        errors = []
        
        search_engine = self._get_engine(engine)
        if not search_engine:
            raise SearchEngineError(f"Unsupported search engine: {engine}")
        
        # Search each legal site
        for site in self.legal_sites[:3]:  # Limit to top 3 sites to avoid rate limits
            try:
                site_results = search_engine.search(
                    query, 
                    num_results=min(num_results, 5),  # Limit per site
                    site_restrict=site
                )
                
                for result in site_results.get('results', []):
                    result['legal_site'] = site
                    all_results.append(result)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except SearchEngineError as e:
                errors.append(f"Error searching {site}: {str(e)}")
                continue
        
        return {
            'results': all_results[:num_results],
            'total_results': len(all_results),
            'errors': errors,
            'engine_used': engine
        }
    
    def search_general(self, query, engine='google', num_results=10):
        """
        General web search with legal context
        
        Args:
            query (str): Search query
            engine (str): Search engine to use
            num_results (int): Number of results
        
        Returns:
            dict: Search results
        """
        search_engine = self._get_engine(engine)
        if not search_engine:
            raise SearchEngineError(f"Unsupported search engine: {engine}")
        
        # Add legal context to query
        legal_query = f"{query} law legal case statute"
        
        try:
            return search_engine.search(legal_query, num_results)
        except SearchEngineError as e:
            # Fallback to original query if legal context fails
            return search_engine.search(query, num_results)
    
    def _get_engine(self, engine_name):
        """Get search engine instance by name"""
        engines = {
            'google': self.google,
            'bing': self.bing,
            'duckduckgo': self.duckduckgo
        }
        return engines.get(engine_name.lower())
    
    def get_available_engines(self):
        """Get list of available search engines"""
        available = []
        
        # Check Google
        if self.google.api_key and self.google.cx:
            available.append('google')
        
        # Check Bing
        if self.bing.api_key:
            available.append('bing')
        
        # DuckDuckGo is always available (no API key required)
        available.append('duckduckgo')
        
        return available

# Utility functions for legal search enhancement
def extract_citations(text):
    """Extract legal citations from text"""
    import re
    
    # Common citation patterns
    patterns = [
        r'\d+\s+[A-Z][a-z\.]+\s+\d+',  # e.g., "123 F.3d 456"
        r'\d+\s+U\.S\.\s+\d+',  # e.g., "123 U.S. 456"
        r'\d+\s+S\.Ct\.\s+\d+',  # e.g., "123 S.Ct. 456"
        r'\d+\s+F\.\d+d\s+\d+',  # e.g., "123 F.3d 456"
    ]
    
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        citations.extend(matches)
    
    return list(set(citations))  # Remove duplicates

def categorize_legal_content(title, snippet):
    """Categorize legal content by type"""
    content = f"{title} {snippet}".lower()
    
    categories = []
    
    # Case law indicators
    if any(word in content for word in ['v.', 'vs.', 'versus', 'court', 'judge', 'ruling']):
        categories.append('Case Law')
    
    # Statute indicators
    if any(word in content for word in ['statute', 'code', 'section', 'usc', 'cfr']):
        categories.append('Statute')
    
    # Regulation indicators
    if any(word in content for word in ['regulation', 'rule', 'cfr', 'federal register']):
        categories.append('Regulation')
    
    # Legal news/analysis
    if any(word in content for word in ['analysis', 'commentary', 'opinion', 'blog', 'news']):
        categories.append('Analysis')
    
    # Forms and documents
    if any(word in content for word in ['form', 'template', 'document', 'contract']):
        categories.append('Forms')
    
    return categories if categories else ['General Legal']