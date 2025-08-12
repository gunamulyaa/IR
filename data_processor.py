#!/usr/bin/env python3
"""
Indonesian News Articles Data Processing and Cleaning Script

This script provides comprehensive data cleaning and processing for the 
combined_articles.json file containing Indonesian news articles.
"""

import json
import re
import pandas as pd
from datetime import datetime
from collections import Counter
import html
import unicodedata
from typing import List, Dict, Any, Optional

class IndonesianNewsProcessor:
    """
    A comprehensive processor for Indonesian news articles data.
    Handles cleaning, validation, normalization, and analysis.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.articles = []
        self.processed_articles = []
        self.statistics = {}
        
    def load_data(self) -> bool:
        """Load the JSON data from file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.articles = json.load(file)
            print(f"✅ Successfully loaded {len(self.articles)} articles")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return False
        except FileNotFoundError:
            print(f"❌ File not found: {self.file_path}")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_data_quality(self) -> Dict[str, Any]:
        """Analyze the quality and characteristics of the data."""
        if not self.articles:
            return {}
        
        stats = {
            'total_articles': len(self.articles),
            'empty_titles': 0,
            'empty_content': 0,
            'malformed_dates': 0,
            'duplicate_titles': 0,
            'content_length_stats': [],
            'title_length_stats': [],
            'date_range': {'earliest': None, 'latest': None},
            'common_words': {},
            'articles_by_month': Counter(),
            'issues_found': []
        }
        
        titles = []
        dates = []
        
        for i, article in enumerate(self.articles):
            # Check for missing or empty fields
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            date_str = article.get('date', '').strip()
            
            if not title:
                stats['empty_titles'] += 1
                stats['issues_found'].append(f"Article {i}: Empty title")
            else:
                titles.append(title)
                stats['title_length_stats'].append(len(title))
            
            if not content:
                stats['empty_content'] += 1
                stats['issues_found'].append(f"Article {i}: Empty content")
            else:
                stats['content_length_stats'].append(len(content))
            
            # Check date format
            if date_str:
                try:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    dates.append(parsed_date)
                    month_key = parsed_date.strftime('%Y-%m')
                    stats['articles_by_month'][month_key] += 1
                except ValueError:
                    stats['malformed_dates'] += 1
                    stats['issues_found'].append(f"Article {i}: Invalid date format: {date_str}")
            else:
                stats['malformed_dates'] += 1
                stats['issues_found'].append(f"Article {i}: Missing date")
        
        # Check for duplicates
        title_counts = Counter(titles)
        stats['duplicate_titles'] = sum(1 for count in title_counts.values() if count > 1)
        
        # Date range
        if dates:
            stats['date_range']['earliest'] = min(dates).isoformat()
            stats['date_range']['latest'] = max(dates).isoformat()
        
        # Content and title length statistics
        if stats['content_length_stats']:
            stats['avg_content_length'] = sum(stats['content_length_stats']) / len(stats['content_length_stats'])
            stats['min_content_length'] = min(stats['content_length_stats'])
            stats['max_content_length'] = max(stats['content_length_stats'])
        
        if stats['title_length_stats']:
            stats['avg_title_length'] = sum(stats['title_length_stats']) / len(stats['title_length_stats'])
            stats['min_title_length'] = min(stats['title_length_stats'])
            stats['max_title_length'] = max(stats['title_length_stats'])
        
        self.statistics = stats
        return stats
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # HTML decode
        text = html.unescape(text)
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might be artifacts
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common formatting artifacts
        text = re.sub(r'\\n', ' ', text)
        text = re.sub(r'\\r', ' ', text)
        text = re.sub(r'\\t', ' ', text)
        
        # Fix multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def validate_date(self, date_str: str) -> Optional[str]:
        """Validate and normalize date format."""
        if not date_str:
            return None
            
        # Try to parse the date
        try:
            parsed_date = datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S')
            return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Try alternative formats
            alternative_formats = [
                '%Y-%m-%d',
                '%d-%m-%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y/%m/%d %H:%M:%S'
            ]
            
            for fmt in alternative_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
        
        return None
    
    def clean_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single article."""
        cleaned = {}
        
        # Clean title
        title = self.clean_text(article.get('title', ''))
        cleaned['title'] = title
        
        # Clean content
        content = self.clean_text(article.get('content', ''))
        cleaned['content'] = content
        
        # Validate and clean date
        date_str = article.get('date', '')
        cleaned_date = self.validate_date(date_str)
        cleaned['date'] = cleaned_date
        
        # Add metadata
        cleaned['original_date'] = date_str
        cleaned['word_count'] = len(content.split()) if content else 0
        cleaned['char_count'] = len(content) if content else 0
        cleaned['has_issues'] = []
        
        # Flag potential issues
        if not title:
            cleaned['has_issues'].append('empty_title')
        if not content:
            cleaned['has_issues'].append('empty_content')
        if not cleaned_date:
            cleaned['has_issues'].append('invalid_date')
        if cleaned['word_count'] < 50:  # Very short articles
            cleaned['has_issues'].append('very_short_content')
        
        return cleaned
    
    def process_all_articles(self) -> List[Dict[str, Any]]:
        """Process and clean all articles."""
        print("🔄 Processing articles...")
        
        self.processed_articles = []
        for i, article in enumerate(self.articles):
            cleaned = self.clean_article(article)
            cleaned['id'] = i + 1
            self.processed_articles.append(cleaned)
            
            if (i + 1) % 100 == 0:
                print(f"   Processed {i + 1}/{len(self.articles)} articles")
        
        print(f"✅ Successfully processed {len(self.processed_articles)} articles")
        return self.processed_articles
    
    def remove_duplicates(self, similarity_threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity."""
        print("🔄 Removing duplicates...")
        
        seen_titles = set()
        unique_articles = []
        duplicate_count = 0
        
        for article in self.processed_articles:
            title = article.get('title', '').lower().strip()
            
            # Simple duplicate detection based on exact title match
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
            else:
                duplicate_count += 1
        
        print(f"✅ Removed {duplicate_count} duplicate articles")
        print(f"✅ Retained {len(unique_articles)} unique articles")
        
        return unique_articles
    
    def filter_articles(self, 
                       min_word_count: int = 10,
                       require_valid_date: bool = True,
                       require_title: bool = True) -> List[Dict[str, Any]]:
        """Filter articles based on quality criteria."""
        print("🔄 Filtering articles...")
        
        filtered_articles = []
        filtered_count = 0
        
        for article in self.processed_articles:
            # Check filtering criteria
            if require_title and not article.get('title', '').strip():
                filtered_count += 1
                continue
                
            if require_valid_date and not article.get('date'):
                filtered_count += 1
                continue
                
            if article.get('word_count', 0) < min_word_count:
                filtered_count += 1
                continue
            
            filtered_articles.append(article)
        
        print(f"✅ Filtered out {filtered_count} articles")
        print(f"✅ Retained {len(filtered_articles)} articles")
        
        return filtered_articles
    
    def save_processed_data(self, output_path: str, articles: List[Dict[str, Any]] = None) -> bool:
        """Save processed data to JSON file."""
        if articles is None:
            articles = self.processed_articles
            
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(articles, file, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(articles)} articles to {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False
    
    def save_to_csv(self, output_path: str, articles: List[Dict[str, Any]] = None) -> bool:
        """Save processed data to CSV file."""
        if articles is None:
            articles = self.processed_articles
            
        try:
            df = pd.DataFrame(articles)
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✅ Saved {len(articles)} articles to CSV: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate a comprehensive data quality report."""
        if not self.statistics:
            self.analyze_data_quality()
        
        stats = self.statistics
        
        report = f"""
📊 INDONESIAN NEWS ARTICLES - DATA QUALITY REPORT
{'='*60}

📈 OVERALL STATISTICS:
   Total Articles: {stats['total_articles']:,}
   Articles with Empty Titles: {stats['empty_titles']:,}
   Articles with Empty Content: {stats['empty_content']:,}
   Articles with Invalid Dates: {stats['malformed_dates']:,}
   Duplicate Titles: {stats['duplicate_titles']:,}

📏 CONTENT STATISTICS:
   Average Content Length: {stats.get('avg_content_length', 0):.0f} characters
   Shortest Content: {stats.get('min_content_length', 0):,} characters
   Longest Content: {stats.get('max_content_length', 0):,} characters
   
   Average Title Length: {stats.get('avg_title_length', 0):.0f} characters
   Shortest Title: {stats.get('min_title_length', 0):,} characters
   Longest Title: {stats.get('max_title_length', 0):,} characters

📅 DATE RANGE:
   Earliest Article: {stats['date_range'].get('earliest', 'N/A')}
   Latest Article: {stats['date_range'].get('latest', 'N/A')}

📊 TOP MONTHS BY ARTICLE COUNT:
"""
        
        for month, count in stats['articles_by_month'].most_common(10):
            report += f"   {month}: {count:,} articles\n"
        
        if stats['issues_found']:
            report += f"\n⚠️  ISSUES FOUND ({len(stats['issues_found'])} total):\n"
            for issue in stats['issues_found'][:20]:  # Show first 20 issues
                report += f"   {issue}\n"
            if len(stats['issues_found']) > 20:
                report += f"   ... and {len(stats['issues_found']) - 20} more issues\n"
        
        return report
    
    def run_full_pipeline(self, 
                         output_json: str = None,
                         output_csv: str = None,
                         min_word_count: int = 10,
                         remove_duplicates: bool = True,
                         require_valid_date: bool = True) -> List[Dict[str, Any]]:
        """Run the complete data processing pipeline."""
        print("🚀 Starting data processing pipeline...")
        print("="*50)
        
        # Step 1: Load data
        if not self.load_data():
            return []
        
        # Step 2: Analyze data quality
        print("\n📊 Analyzing data quality...")
        self.analyze_data_quality()
        print(self.generate_report())
        
        # Step 3: Process articles
        self.process_all_articles()
        
        # Step 4: Remove duplicates (optional)
        if remove_duplicates:
            processed_articles = self.remove_duplicates()
        else:
            processed_articles = self.processed_articles
        
        # Step 5: Filter articles
        final_articles = self.filter_articles(
            min_word_count=min_word_count,
            require_valid_date=require_valid_date
        )
        
        # Step 6: Save results
        if output_json:
            self.save_processed_data(output_json, final_articles)
        
        if output_csv:
            self.save_to_csv(output_csv, final_articles)
        
        print("\n✅ Pipeline completed successfully!")
        print(f"📊 Final dataset: {len(final_articles)} clean articles")
        
        return final_articles


def main():
    """Main function to run the data processing pipeline."""
    
    # Initialize processor
    input_file = "c:\\Users\\PC 3\\Documents\\GitHub\\IR\\Data\\combined_articles.json"
    processor = IndonesianNewsProcessor(input_file)
    
    # Run the complete pipeline
    cleaned_articles = processor.run_full_pipeline(
        output_json="c:\\Users\\PC 3\\Documents\\GitHub\\IR\\Data\\cleaned_articles.json",
        output_csv="c:\\Users\\PC 3\\Documents\\GitHub\\IR\\Data\\cleaned_articles.csv",
        min_word_count=20,  # Minimum 20 words per article
        remove_duplicates=True,
        require_valid_date=True
    )
    
    print("\n🎯 PROCESSING SUMMARY:")
    print(f"   Original articles: {len(processor.articles)}")
    print(f"   Cleaned articles: {len(cleaned_articles)}")
    print(f"   Improvement: {((len(cleaned_articles)/len(processor.articles))*100):.1f}% retained")
    
    # Additional analysis
    print("\n📋 SAMPLE OF CLEANED DATA:")
    for i, article in enumerate(cleaned_articles[:3]):
        print(f"\n   Article {i+1}:")
        print(f"   Title: {article['title'][:100]}...")
        print(f"   Date: {article['date']}")
        print(f"   Word Count: {article['word_count']}")
        print(f"   Issues: {article['has_issues'] if article['has_issues'] else 'None'}")


if __name__ == "__main__":
    main()
