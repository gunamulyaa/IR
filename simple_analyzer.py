#!/usr/bin/env python3
"""
Simple Indonesian News Articles Data Analysis

A straightforward script to analyze and clean the combined_articles.json file.
"""

import json
import re
from datetime import datetime
from collections import Counter

def load_articles(file_path):
    """Load articles from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            articles = json.load(file)
        print(f"✅ Loaded {len(articles)} articles")
        return articles
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return []

def analyze_articles(articles):
    """Analyze the articles for basic statistics."""
    print("\n📊 BASIC ANALYSIS:")
    print(f"Total articles: {len(articles)}")
    
    # Count articles with missing data
    empty_titles = sum(1 for a in articles if not a.get('title', '').strip())
    empty_content = sum(1 for a in articles if not a.get('content', '').strip())
    empty_dates = sum(1 for a in articles if not a.get('date', '').strip())
    
    print(f"Articles with empty titles: {empty_titles}")
    print(f"Articles with empty content: {empty_content}")
    print(f"Articles with empty dates: {empty_dates}")
    
    # Analyze content lengths
    content_lengths = [len(a.get('content', '')) for a in articles if a.get('content')]
    if content_lengths:
        print(f"Average content length: {sum(content_lengths)/len(content_lengths):.0f} characters")
        print(f"Shortest article: {min(content_lengths)} characters")
        print(f"Longest article: {max(content_lengths)} characters")
    
    # Analyze dates
    valid_dates = []
    for article in articles:
        date_str = article.get('date', '').strip()
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                valid_dates.append(date_obj)
            except ValueError:
                pass
    
    if valid_dates:
        print(f"Valid dates found: {len(valid_dates)}")
        print(f"Date range: {min(valid_dates).date()} to {max(valid_dates).date()}")
    
    return {
        'total': len(articles),
        'empty_titles': empty_titles,
        'empty_content': empty_content,
        'empty_dates': empty_dates,
        'valid_dates': len(valid_dates)
    }

def clean_text(text):
    """Clean text content."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove common artifacts
    text = re.sub(r'\\[nrt]', ' ', text)
    text = re.sub(r' +', ' ', text)
    
    return text

def clean_articles(articles):
    """Clean all articles."""
    print("\n🔄 Cleaning articles...")
    
    cleaned = []
    issues_count = 0
    
    for i, article in enumerate(articles):
        cleaned_article = {}
        
        # Clean title
        title = clean_text(article.get('title', ''))
        cleaned_article['title'] = title
        
        # Clean content
        content = clean_text(article.get('content', ''))
        cleaned_article['content'] = content
        
        # Keep original date for now
        cleaned_article['date'] = article.get('date', '')
        
        # Add metadata
        cleaned_article['id'] = i + 1
        cleaned_article['word_count'] = len(content.split()) if content else 0
        
        # Flag issues
        issues = []
        if not title:
            issues.append('no_title')
        if not content:
            issues.append('no_content')
        if not cleaned_article['date']:
            issues.append('no_date')
        if cleaned_article['word_count'] < 10:
            issues.append('very_short')
        
        cleaned_article['issues'] = issues
        if issues:
            issues_count += 1
        
        cleaned.append(cleaned_article)
    
    print(f"✅ Cleaned {len(cleaned)} articles")
    print(f"⚠️  {issues_count} articles have issues")
    
    return cleaned

def filter_quality_articles(articles, min_words=20):
    """Filter articles to keep only high-quality ones."""
    print(f"\n🔍 Filtering articles (minimum {min_words} words)...")
    
    quality_articles = []
    
    for article in articles:
        if (article.get('title', '').strip() and 
            article.get('content', '').strip() and 
            article.get('word_count', 0) >= min_words and
            article.get('date', '').strip()):
            quality_articles.append(article)
    
    print(f"✅ Kept {len(quality_articles)} quality articles")
    print(f"🗑️  Filtered out {len(articles) - len(quality_articles)} articles")
    
    return quality_articles

def save_results(articles, output_file):
    """Save processed articles to file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(articles, file, ensure_ascii=False, indent=2)
        print(f"✅ Saved {len(articles)} articles to {output_file}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def show_sample_articles(articles, count=3):
    """Show sample articles."""
    print(f"\n📋 SAMPLE ARTICLES (first {count}):")
    
    for i, article in enumerate(articles[:count]):
        print(f"\n--- Article {i+1} ---")
        print(f"Title: {article.get('title', 'N/A')[:100]}...")
        print(f"Date: {article.get('date', 'N/A')}")
        print(f"Word count: {article.get('word_count', 0)}")
        print(f"Issues: {', '.join(article.get('issues', [])) or 'None'}")
        if article.get('content'):
            print(f"Content preview: {article['content'][:200]}...")

def main():
    """Main function."""
    print("🚀 INDONESIAN NEWS ARTICLES - DATA PROCESSING")
    print("=" * 50)
    
    # File paths
    input_file = "Data/combined_articles.json"
    output_file = "Data/cleaned_articles.json"
    
    # Step 1: Load data
    articles = load_articles(input_file)
    if not articles:
        return
    
    # Step 2: Analyze original data
    stats = analyze_articles(articles)
    
    # Step 3: Clean articles
    cleaned_articles = clean_articles(articles)
    
    # Step 4: Filter for quality
    quality_articles = filter_quality_articles(cleaned_articles, min_words=15)
    
    # Step 5: Show samples
    show_sample_articles(quality_articles)
    
    # Step 6: Save results
    save_results(quality_articles, output_file)
    
    # Final summary
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"Original articles: {len(articles)}")
    print(f"Quality articles: {len(quality_articles)}")
    print(f"Retention rate: {(len(quality_articles)/len(articles)*100):.1f}%")
    
    # Common topics analysis
    print(f"\n📈 CONTENT INSIGHTS:")
    all_titles = [a['title'].lower() for a in quality_articles if a.get('title')]
    
    # Simple keyword frequency
    common_words = Counter()
    for title in all_titles:
        words = re.findall(r'\b\w+\b', title)
        common_words.update([w for w in words if len(w) > 3])
    
    print("Most common words in titles:")
    for word, count in common_words.most_common(10):
        print(f"  {word}: {count}")

if __name__ == "__main__":
    main()
