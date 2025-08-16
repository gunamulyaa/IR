"""
Search Analytics and Monitoring Module
"""
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAnalytics:
    """Search analytics and monitoring"""
    
    def __init__(self, log_file: str = "search_analytics.jsonl"):
        self.log_file = log_file
        
    def log_search(self, 
                   query: str, 
                   search_type: str, 
                   results_count: int, 
                   execution_time: float,
                   user_ip: str = None):
        """Log search query and results"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "search_type": search_type,
                "results_count": results_count,
                "execution_time_ms": round(execution_time * 1000, 2),
                "user_ip": user_ip,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "hour": datetime.now().hour
            }
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log search: {str(e)}")
    
    def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics summary"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Read log entries
            entries = []
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_date = datetime.fromisoformat(entry["timestamp"])
                            if entry_date >= cutoff_date:
                                entries.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            if not entries:
                return {"error": "No search data found"}
            
            # Calculate metrics
            total_searches = len(entries)
            avg_execution_time = sum(e["execution_time_ms"] for e in entries) / total_searches
            avg_results = sum(e["results_count"] for e in entries) / total_searches
            
            # Query analysis
            query_lengths = [len(e["query"].split()) for e in entries]
            avg_query_length = sum(query_lengths) / len(query_lengths)
            
            # Search type distribution
            search_types = Counter(e["search_type"] for e in entries)
            
            # Most common queries
            queries = Counter(e["query"].lower() for e in entries)
            top_queries = queries.most_common(10)
            
            # Hourly distribution
            hourly_dist = Counter(e["hour"] for e in entries)
            
            # Daily trend (last 7 days)
            recent_entries = [e for e in entries if 
                            datetime.fromisoformat(e["timestamp"]) >= datetime.now() - timedelta(days=7)]
            daily_counts = Counter(e["date"] for e in recent_entries)
            
            return {
                "period_days": days,
                "total_searches": total_searches,
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "avg_results_per_search": round(avg_results, 1),
                "avg_query_length_words": round(avg_query_length, 1),
                "search_type_distribution": dict(search_types),
                "top_queries": top_queries,
                "hourly_distribution": dict(hourly_dist),
                "daily_trend": dict(daily_counts)
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Read recent entries (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_searches = []
            
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if entry_time >= cutoff_time:
                                recent_searches.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            if not recent_searches:
                return {"message": "No recent search data"}
            
            # Performance metrics
            execution_times = [e["execution_time_ms"] for e in recent_searches]
            
            return {
                "last_24h_searches": len(recent_searches),
                "avg_response_time_ms": round(sum(execution_times) / len(execution_times), 2),
                "min_response_time_ms": min(execution_times),
                "max_response_time_ms": max(execution_times),
                "p95_response_time_ms": round(sorted(execution_times)[int(0.95 * len(execution_times))], 2),
                "slow_queries_count": len([t for t in execution_times if t > 1000]),  # > 1 second
                "zero_results_count": len([e for e in recent_searches if e["results_count"] == 0])
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {"error": str(e)}

def display_analytics_dashboard():
    """Display analytics dashboard in Streamlit"""
    st.header("📊 Search Analytics Dashboard")
    
    # Initialize analytics
    analytics = SearchAnalytics()
    
    # Time period selector
    period = st.selectbox("Analytics Period", [7, 30, 90], index=1)
    
    # Get analytics data
    summary = analytics.get_analytics_summary(days=period)
    performance = analytics.get_performance_metrics()
    
    if "error" not in summary:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Searches", summary["total_searches"])
        with col2:
            st.metric("Avg Response Time", f"{summary['avg_execution_time_ms']:.0f} ms")
        with col3:
            st.metric("Avg Results", f"{summary['avg_results_per_search']:.1f}")
        with col4:
            st.metric("Avg Query Length", f"{summary['avg_query_length_words']:.1f} words")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Search type distribution
            st.subheader("🔍 Search Type Distribution")
            search_types = summary["search_type_distribution"]
            if search_types:
                st.bar_chart(search_types)
            else:
                st.info("No search type data available")
        
        with col2:
            # Hourly distribution
            st.subheader("⏰ Search Activity by Hour")
            hourly_data = summary["hourly_distribution"]
            if hourly_data:
                # Convert to proper format for bar chart
                hours = list(range(24))
                counts = [hourly_data.get(h, 0) for h in hours]
                chart_data = {f"{h:02d}:00": counts[h] for h in hours}
                st.bar_chart(chart_data)
            else:
                st.info("No hourly data available")
        
        # Top queries
        st.subheader("🔥 Most Popular Queries")
        top_queries = summary["top_queries"]
        if top_queries:
            for i, (query, count) in enumerate(top_queries[:10], 1):
                st.write(f"{i}. **{query}** ({count} times)")
        else:
            st.info("No query data available")
        
        # Daily trend
        st.subheader("📈 Search Trend (Last 7 Days)")
        daily_trend = summary["daily_trend"]
        if daily_trend:
            st.bar_chart(daily_trend)
        else:
            st.info("No trend data available")
    
    else:
        st.warning(f"Analytics data not available: {summary.get('error', 'Unknown error')}")
    
    # Performance metrics
    st.subheader("⚡ Performance Metrics (Last 24 Hours)")
    if "error" not in performance:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Searches (24h)", performance.get("last_24h_searches", "N/A"))
            st.metric("P95 Response Time", f"{performance.get('p95_response_time_ms', 0):.0f} ms")
        
        with col2:
            st.metric("Avg Response Time", f"{performance.get('avg_response_time_ms', 0):.0f} ms")
            st.metric("Slow Queries", performance.get("slow_queries_count", "N/A"))
        
        with col3:
            st.metric("Min Response Time", f"{performance.get('min_response_time_ms', 0):.0f} ms")
            st.metric("Zero Results", performance.get("zero_results_count", "N/A"))
    
    else:
        st.info("Performance data not available for the last 24 hours")

# Export analytics instance
search_analytics = SearchAnalytics()
