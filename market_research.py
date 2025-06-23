# type: ignore
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import time

def _google_search_urls(query: str, num_results: int = 5) -> list[str]:
    """Internal helper to search Google and return top URLs."""
    try:
        urls = list(search(query, num_results=num_results, sleep_interval=2))
        return urls
    except Exception as e:
        print(f"Google search failed: {e}")
        return []

def _browse_and_clean_pages(urls: list[str]) -> tuple[list[str], list[str]]:
    """Internal helper to browse a list of URLs and return their cleaned, quality-filtered text content."""
    extracted_texts = []
    successful_urls = []
    seen_content_hashes = set()  # For deduplication
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in urls:
        try:
            print(f"Browsing: {url}")
            
            # Implement exponential backoff for retries
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=15, headers=headers)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt == 2:
                        raise e
                    time.sleep(2 ** attempt)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Extract article content with priority to main content areas
            content = None
            for selector in ['article', 'main', '[role="main"]', '.content', '#content']:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                content = soup
            
            # Get text and clean it up
            text = content.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk and len(chunk) > 40)  # Filter short lines
            
            # Skip if content is too short or likely not meaningful
            if len(text.split()) < 100:
                print(f"Skipping {url}: Content too short or low quality")
                continue
            
            # Check for duplicate content
            content_hash = hash(text)
            if content_hash in seen_content_hashes:
                print(f"Skipping {url}: Duplicate content detected")
                continue
            seen_content_hashes.add(content_hash)
            
            extracted_texts.append(text)
            successful_urls.append(url)
            
            # Adaptive rate limiting based on successful requests
            time.sleep(1.5)  # Increased sleep interval for politeness
            
        except Exception as e:
            print(f"Failed to retrieve content from {url}: {e}")
            
    return successful_urls, extracted_texts

from google_services import generate_gemini_summary

def _evaluate_source_credibility(url: str) -> float:
    """Evaluates source credibility based on domain and URL characteristics."""
    credibility_score = 1.0
    
    # Prefer established domains
    established_domains = ['.edu', '.gov', '.org']
    for domain in established_domains:
        if domain in url:
            credibility_score *= 1.2
    
    # Prefer known business/tech domains
    business_domains = ['bloomberg.com', 'reuters.com', 'forbes.com', 'businesswire.com']
    if any(domain in url.lower() for domain in business_domains):
        credibility_score *= 1.3
    
    # Penalize less reliable indicators
    if 'blog' in url.lower():
        credibility_score *= 0.9
    if sum(c == '/' for c in url) > 4:  # Deep links might be less authoritative
        credibility_score *= 0.95
        
    return credibility_score

def _generate_combined_summary(urls: list[str], texts: list[str]) -> str:
    """Generates a coherent summary combining insights from all sources using Gemini AI."""
    if not urls or not texts:
        return "No valid content to summarize."
    
    try:
        # Weight sources by credibility
        credibility_scores = [_evaluate_source_credibility(url) for url in urls]
        
        # Normalize weights
        total_score = sum(credibility_scores)
        weights = [score/total_score for score in credibility_scores]
        
        # Combine text with weighted importance
        chunks = []
        for text, weight in zip(texts, weights):
            # Select most relevant portions based on weight
            words = text.split()
            chunk_size = int(min(2000, len(words) * weight))  # Limit chunk size
            chunk = " ".join(words[:chunk_size])
            chunks.append(chunk)
        
        combined_text = "\n\n---\n\n".join(chunks)
        
        # Adjust temperature based on source diversity
        temperature = min(0.7, 0.5 + (len(set(urls)) / 10))  # More sources = slightly higher temperature
        
        # Get AI-generated summary
        ai_summary = generate_gemini_summary(
            text=combined_text,
            prompt_type="market_research",
            temperature=temperature
        )
        
        # Format final summary with credibility-weighted sources
        summary_lines = [
            "Market Research Summary (AI-generated from weighted sources):",
            "",
            ai_summary,
            "",
            "Sources (by credibility):"
        ]
        
        # Sort sources by credibility score
        credible_sources = sorted(zip(urls, credibility_scores), key=lambda x: x[1], reverse=True)
        for i, (url, score) in enumerate(credible_sources, 1):
            summary_lines.append(f"{i}. {url} (credibility: {score:.2f})")
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return (
            f"Market Research Summary (Fallback):\n\n"
            f"Analyzed {len(urls)} sources but AI summarization failed.\n"
            f"Sources:\n" + "\n".join(f"{i}. {url}" for i, url in enumerate(urls, 1))
        )

def conduct_market_research(topic: str) -> str:
    """
    Performs market research on a given topic by searching for relevant articles,
    reading their content, and returning the combined text for summarization.
    """
    print(f"Starting market research for: {topic}...")
    
    # 1. Search
    urls_to_browse = _google_search_urls(f"market research and trends for {topic}")
    if not urls_to_browse:
        return "Could not find any relevant articles for the topic."
        
    # 2. Browse & Clean
    successful_urls, extracted_texts = _browse_and_clean_pages(urls_to_browse)
    if not successful_urls:
        return "Found articles, but could not extract any readable content."
        
    # 3. Generate and return combined summary
    return _generate_combined_summary(successful_urls, extracted_texts)