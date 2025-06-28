
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import time

def _google_search_urls(topic: str, num_results: int = 10) -> list[str]:
    """
    🔍 Enhanced Web Search Helper
    
    Generates diverse search queries for a topic and returns aggregated, unique URLs.
    Features:
    - 🎯 Multiple query strategies
    - 🔄 Duplicate removal
    - ⚡ Smart rate limiting
    - 🛡️ Error handling
    """
    # Helper function to count words
    def count_words(text: str) -> int:
        return len(text.split())
    
    # Determine query strategy based on topic length
    word_count = count_words(topic)
    is_long_topic = word_count >= 4
    
    # Generate search queries based on topic length
    if is_long_topic:
        # For specific long-tail topics, use simpler variations
        search_queries = [
            topic,  # Use the topic as-is
            f"{topic} analysis",
            f"{topic} news",
            f"{topic} discussions"
        ]
    else:
        # For shorter topics, use more diverse query variations
        search_queries = [
            f"{topic} market trends",
            f"venture capital funding for {topic}",
            f"innovative applications in {topic}",
            f"academic research papers on {topic}",
            f"challenges of adoption for {topic}"
        ]
    
    all_urls = set()  # Use set for automatic deduplication
    
    for query in search_queries:
        try:
            print(f"🔍 Searching: {query}")
            urls = [str(result) for result in search(query, num_results=num_results, sleep_interval=2)]
            all_urls.update(urls)  # Add new URLs to set
            time.sleep(2)  # Be polite between queries
        except Exception as e:
            print(f"Google search failed for query '{query}': {e}")
            continue
    
    return list(all_urls)

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
    
    Creates a comprehensive summary using map-reduce strategy:
    - 🗺️ Map: Generate individual summaries for each source
    - 🔄 Reduce: Combine summaries into cohesive analysis
    - ⭐ Sort sources by credibility
    - 📊 Present structured insights
    """
    if not urls or not texts:
        return "No valid content to summarize."
    
    try:
        # Calculate credibility scores (only used for source sorting)
        credibility_scores = [_evaluate_source_credibility(url) for url in urls]
        
        # MAP STEP: Generate individual summaries
        individual_summaries = []
        for text in texts:
            try:
                summary = generate_gemini_summary(
                    text=text,
                    prompt_type="summarize_article",
                    temperature=0.5
                )
                individual_summaries.append(summary)
            except Exception as e:
                print(f"⚠️ Skipping summary for one source due to an API error: {e}")
                continue
        
        # REDUCE STEP: Combine individual summaries
        combined_summaries = "\n\n---\n\n".join(individual_summaries)
        
        # Generate final synthesized summary with hierarchical structure
        ai_summary = generate_gemini_summary(
            text=combined_summaries,
            prompt_type="market_research",
            temperature=0.7
        )
        
        # Format final summary with credibility-sorted sources
        summary_lines = [
            "# 📊 Market Research Insights",
            "",
            "## 🤖 AI-Generated Analysis",
            ai_summary,
            "",
            "## 📚 Sources by Credibility Rating"
        ]
        
        # Sort sources by credibility score
        credible_sources = sorted(zip(urls, credibility_scores), key=lambda x: x[1], reverse=True)
        for i, (url, score) in enumerate(credible_sources, 1):
            # Clean up URL to prevent line breaks
            cleaned_url = url.replace('\n', '').replace('\r', '')
            # Add star rating based on credibility score
            stars = "⭐" * min(5, int(score * 2.5))
            # Append formatted string with a simple hyphen and no bullet point
            summary_lines.append(f"[{cleaned_url}]({cleaned_url}) - Rating: {stars} ({score:.2f})")
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
        return (
            "# ⚠️ Market Research Summary (Limited)\n\n"
            f"📚 Analyzed {len(urls)} sources but couldn't generate AI summary.\n\n"
            "## 🔍 Raw Sources\n" +
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
    urls_to_browse = _google_search_urls(topic)
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