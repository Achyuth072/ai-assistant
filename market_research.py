
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import time

def _google_search_urls(query: str, num_results: int = 5) -> list[str]:
    """
    🔍 Web Search Helper
    
    Searches Google for relevant content and returns top quality URLs.
    Includes smart rate limiting and error handling.
    """
    try:
        urls = [str(result) for result in search(query, num_results=num_results, sleep_interval=2)]
        return urls
    except Exception as e:
        print(f"Google search failed: {e}")
        return []

def _browse_and_clean_pages(urls: list[str]) -> tuple[list[str], list[str]]:
    """
    🌐 Smart Web Content Extractor
    
    Intelligently browses URLs and extracts clean, high-quality content:
    - ✨ Removes ads and clutter
    - 🔄 Handles duplicates
    - 📊 Quality filtering
    - ⚡ Optimized loading
    - 🛡️ Error handling
    """
    extracted_texts = []
    successful_urls = []
    seen_content_hashes = set()  # For deduplication
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in urls:
        try:
            print(f"📑 Analyzing: {url}")
            
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
                print(f"⏩ Skipping {url}: Content too short or low quality")
                continue
            
            # Check for duplicate content
            content_hash = hash(text)
            if content_hash in seen_content_hashes:
                print(f"🔄 Skipping {url}: Duplicate content detected")
                continue
            seen_content_hashes.add(content_hash)
            
            extracted_texts.append(text)
            successful_urls.append(url)
            
            # Adaptive rate limiting based on successful requests
            time.sleep(1.5)  # Increased sleep interval for politeness
            
        except Exception as e:
            print(f"❌ Failed to retrieve content from {url}: {e}")
            
    return successful_urls, extracted_texts

from google_services import generate_gemini_summary

def _evaluate_source_credibility(url: str) -> float:
    """
    ⭐ Source Credibility Analyzer
    
    Calculates trustworthiness scores for information sources using:
    - 🏛️ Domain reputation
    - 🎓 Educational/Government status
    - 📰 Professional news sources
    - 📊 URL structure quality
    """
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
    """
    🤖 AI Research Synthesizer
    
    Creates an intelligent, weighted summary from multiple sources:
    - 🎯 Prioritizes credible sources
    - 🔄 Combines multiple perspectives
    - 📊 Adjusts for source quality
    - 🎨 Creates readable output
    """
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
            "📊 Market Research Insights",
            "══════════════════════",
            "",
            "🤖 AI-Generated Analysis:",
            "─────────────────────",
            ai_summary,
            "",
            "📚 Sources by Credibility Rating:",
            "────────────────────────────"
        ]
        
        # Sort sources by credibility score
        credible_sources = sorted(zip(urls, credibility_scores), key=lambda x: x[1], reverse=True)
        for i, (url, score) in enumerate(credible_sources, 1):
            # Add star rating based on credibility score
            stars = "⭐" * min(5, int(score * 2.5))
            summary_lines.append(f"{i}. {url}")
            summary_lines.append(f"   Rating: {stars} ({score:.2f})")
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return (
            "⚠️ Market Research Summary (Limited)\n"
            "══════════════════════════════\n\n"
            f"📚 Analyzed {len(urls)} sources but couldn't generate AI summary.\n"
            f"🔍 Raw Sources:\n" +
            "\n".join(f"{i}. {url}" for i, url in enumerate(urls, 1))
        )

def conduct_market_research(topic: str) -> str:
    """
    📊 Automated Market Research Assistant
    
    Conducts comprehensive market research through:
    - 🔍 Intelligent web searching
    - 📚 Content analysis
    - ⭐ Source evaluation
    - 🤖 AI-powered summarization
    
    Perfect for:
    - 📈 Market trend analysis
    - 🎯 Competitor research
    - 🌐 Industry insights
    - 💡 Innovation tracking
    """
    print(f"\n🔍 Starting Market Research")
    print("════════════════════════")
    print(f"📊 Topic: {topic}")
    print("\n🔄 Phase 1: Gathering Sources...")
    urls_to_browse = _google_search_urls(f"market research and trends for {topic}")
    if not urls_to_browse:
        return "❌ Could not find any relevant articles. Please try a different search term or check your internet connection."
        
    # 2. Browse & Clean
    print("\n🔄 Phase 2: Analyzing Content...")
    successful_urls, extracted_texts = _browse_and_clean_pages(urls_to_browse)
    if not successful_urls:
        return "📑 Found articles, but couldn't extract meaningful content. This might be due to website restrictions or non-standard formatting."
        
    # 3. Generate and return combined summary
    print("\n🔄 Phase 3: Generating Insights...")
    result = _generate_combined_summary(successful_urls, extracted_texts)
    print("\n✅ Research Complete!\n")
    return result