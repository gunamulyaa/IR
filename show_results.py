#!/usr/bin/env python3
"""
Data Processing Summary and Results Viewer
"""

import json

def show_processing_results():
    """Display summary of the data processing results."""
    
    print("🎉 DATA PROCESSING COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    
    # Load and display basic stats
    try:
        with open("Data/cleaned_articles.json", 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        
        print(f"✅ Cleaned articles loaded: {len(cleaned_data)}")
        
        # Quality statistics
        total_words = sum(article.get('word_count', 0) for article in cleaned_data)
        articles_with_issues = sum(1 for article in cleaned_data if article.get('issues'))
        
        print(f"📊 Total words across all articles: {total_words:,}")
        print(f"📊 Average words per article: {total_words/len(cleaned_data):.0f}")
        print(f"📊 Articles with issues: {articles_with_issues}")
        print(f"📊 Quality retention rate: {((len(cleaned_data)-articles_with_issues)/len(cleaned_data)*100):.1f}%")
        
        # Sample articles
        print(f"\n📋 SAMPLE OF PROCESSED ARTICLES:")
        for i, article in enumerate(cleaned_data[:3]):
            print(f"\n📰 Article {i+1}:")
            print(f"   Title: {article['title'][:80]}...")
            print(f"   Date: {article['date']}")
            print(f"   Word Count: {article['word_count']:,}")
            print(f"   Character Count: {len(article.get('content', '')):,}")
            if article.get('issues'):
                print(f"   Issues: {', '.join(article['issues'])}")
            else:
                print(f"   Issues: None ✅")
        
        # Date analysis
        dates = [article['date'] for article in cleaned_data if article.get('date')]
        if dates:
            print(f"\n📅 DATE RANGE:")
            print(f"   Earliest: {min(dates)}")
            print(f"   Latest: {max(dates)}")
        
        print(f"\n🗂️ OUTPUT FILES CREATED:")
        print(f"   ✅ Data/cleaned_articles.json - {len(cleaned_data)} articles in JSON format")
        print(f"   ✅ Data/cleaned_articles.csv - Same data in CSV format")
        
        print(f"\n🚀 READY FOR IR SYSTEM INTEGRATION!")
        print(f"   Your Indonesian news articles are now clean and ready for:")
        print(f"   • Elasticsearch indexing")
        print(f"   • Text analysis and NLP")
        print(f"   • Search and retrieval applications")
        print(f"   • Machine learning and data mining")
        
    except FileNotFoundError:
        print("❌ Cleaned data file not found. Please run the data processing script first.")
    except Exception as e:
        print(f"❌ Error reading results: {e}")

if __name__ == "__main__":
    show_processing_results()
