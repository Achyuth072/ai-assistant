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
    """Internal helper to browse a list of URLs and return their cleaned text content."""
    extracted_texts = []
    successful_urls = []
    for url in urls:
        try:
            print(f"Browsing: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            extracted_texts.append(text)
            successful_urls.append(url)
            time.sleep(1) # Be a good internet citizen
            
        except Exception as e:
            print(f"Failed to retrieve content from {url}: {e}")
            
    return successful_urls, extracted_texts

from google_services import generate_gemini_summary

def _generate_combined_summary(urls: list[str], texts: list[str]) -> str:
    """Generates a coherent summary combining insights from all sources using Gemini AI."""
    if not urls or not texts:
        return "No valid content to summarize."
    
    # Combine all text for summarization
    combined_text = "\n\n".join(texts)
    
    try:
        # Get AI-generated summary using gemini-2.0-flash with market research prompt
        ai_summary = generate_gemini_summary(
            text=combined_text,
            prompt_type="market_research",
            model_name="gemini-2.0-flash"
        )
        
        # Format final summary with sources
        summary = (
            f"Market Research Summary (AI-generated from {len(urls)} sources):\n\n"
            f"{ai_summary}\n\n"
            f"Sources:\n"
        )
        
        # Add source citations
        for i, url in enumerate(urls, 1):
            summary += f"{i}. {url}\n"
            
        return summary
        
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