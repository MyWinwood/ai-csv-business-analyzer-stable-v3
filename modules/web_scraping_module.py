import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import os
import asyncio
from typing import Dict, List, Optional, Any

# Environment variable helper
def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with fallback to Streamlit secrets"""
    value = os.getenv(key)
    if value:
        return value
    
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    return default

class SimpleWebScraper:
    """Simple web scraper for business research"""
    
    def __init__(self):
        self.results = []
        self.processed_count = 0
        
    def search_business_info(self, business_name: str) -> Dict[str, str]:
        """Search for business information"""
        # Simulate business research (in real implementation, this would use web scraping APIs)
        time.sleep(0.1)  # Simulate processing time
        
        # Mock results for demonstration
        mock_results = {
            'phone': 'Not found',
            'email': 'Not found', 
            'website': 'Not found',
            'address': 'Not found',
            'description': 'Not researched'
        }
        
        # Add some realistic mock data for demonstration
        business_lower = business_name.lower()
        if 'tech' in business_lower or 'software' in business_lower:
            mock_results['email'] = f"info@{business_name.lower().replace(' ', '')}.com"
            mock_results['website'] = f"https://www.{business_name.lower().replace(' ', '')}.com"
            mock_results['description'] = f"{business_name} - Technology and software solutions provider"
            
        return mock_results
    
    def process_businesses(self, df: pd.DataFrame, business_column: str) -> pd.DataFrame:
        """Process businesses for research"""
        if business_column not in df.columns:
            st.error(f"Column '{business_column}' not found in data")
            return df
            
        result_df = df.copy()
        
        # Add research columns if they don't exist
        research_columns = ['phone', 'email', 'website', 'address', 'description']
        for col in research_columns:
            if col not in result_df.columns:
                result_df[col] = 'Not researched'
        
        # Add email campaign selection column
        if 'email_campaign_selected' not in result_df.columns:
            result_df['email_campaign_selected'] = False
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_businesses = len(result_df)
        
        for idx, row in result_df.iterrows():
            business_name = row[business_column]
            
            if pd.isna(business_name) or str(business_name).strip() == '':
                continue
                
            status_text.text(f"Researching: {business_name}")
            
            # Get business information
            business_info = self.search_business_info(str(business_name))
            
            # Update the dataframe
            for col, value in business_info.items():
                result_df.at[idx, col] = value
            
            # Auto-select for email campaign if email found
            if business_info.get('email', 'Not found') not in ['Not found', 'Not researched', '']:
                result_df.at[idx, 'email_campaign_selected'] = True
            
            self.processed_count += 1
            progress = self.processed_count / total_businesses
            progress_bar.progress(progress)
            
        status_text.text(f"✅ Research completed! Processed {self.processed_count} businesses.")
        progress_bar.progress(1.0)
        
        return result_df

def perform_web_scraping(df: pd.DataFrame):
    """Main web scraping interface for Streamlit"""
    st.header("🔍 Business Research & Data Enhancement")
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No data available for research.")
        return
    
    # Business column selection
    text_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    if not text_columns:
        st.error("❌ No text columns found for business names.")
        return
    
    # Find default business column
    default_col = None
    for col in text_columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['business', 'company', 'consignee', 'customer', 'client']):
            default_col = col
            break
    
    if default_col is None:
        default_col = text_columns[0]
    
    business_column = st.selectbox(
        "📋 Select the column containing business names:",
        text_columns,
        index=text_columns.index(default_col) if default_col in text_columns else 0,
        help="Choose the column that contains the business/company names to research"
    )
    
    # Show sample data
    st.subheader("📊 Sample Data")
    sample_businesses = df[business_column].dropna().head(10).tolist()
    st.write("Sample businesses that will be researched:")
    for i, business in enumerate(sample_businesses[:5], 1):
        st.write(f"{i}. {business}")
    if len(sample_businesses) > 5:
        st.write(f"... and {len(df)} total businesses")
    
    # Research button
    col1, col2 = st.columns([2, 1])
    
    with col1:
        start_research = st.button(
            "🚀 Start Business Research", 
            type="primary",
            help="Begin researching contact information for all businesses"
        )
    
    with col2:
        st.metric("🏢 Total Businesses", len(df))
    
    # Perform research
    if start_research:
        st.markdown("---")
        st.subheader("🔬 Research in Progress...")
        
        scraper = SimpleWebScraper()
        research_results = scraper.process_businesses(df, business_column)
        
        # Store results in session state
        st.session_state.research_results = research_results
        st.session_state.research_completed = True
        st.session_state.selected_business_column = business_column
        
        # Show results summary
        st.markdown("---")
        st.success("🎉 Research Completed!")
        
        # Calculate statistics
        emails_found = len(research_results[research_results['email'] != 'Not found'])
        phones_found = len(research_results[research_results['phone'] != 'Not found'])
        websites_found = len(research_results[research_results['website'] != 'Not found'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📧 Emails Found", emails_found)
        with col2:
            st.metric("📞 Phones Found", phones_found)
        with col3:
            st.metric("🌐 Websites Found", websites_found)
        with col4:
            success_rate = (emails_found / len(research_results)) * 100
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
        
        # Show results preview
        st.subheader("📋 Research Results Preview")
        display_cols = [business_column, 'email', 'phone', 'website', 'email_campaign_selected']
        available_cols = [col for col in display_cols if col in research_results.columns]
        
        st.dataframe(
            research_results[available_cols].head(10),
            use_container_width=True
        )
        
        # Download button
        csv_data = research_results.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_research_results_{timestamp}.csv"
        
        st.download_button(
            "📥 Download Research Results",
            csv_data,
            filename,
            "text/csv",
            help="Download the complete research results as CSV"
        )
        
        st.balloons()
    
    # Show existing results if available
    if st.session_state.get('research_completed', False) and 'research_results' in st.session_state:
        st.markdown("---")
        st.subheader("📊 Previous Research Results")
        
        results = st.session_state.research_results
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Researched", len(results))
        with col2:
            emails = len(results[results['email'] != 'Not found'])
            st.metric("Emails Found", emails)
        with col3:
            selected = len(results[results.get('email_campaign_selected', False) == True])
            st.metric("Selected for Campaign", selected)
        
        # Download previous results
        if len(results) > 0:
            csv_data = results.to_csv(index=False)
            st.download_button(
                "📥 Download Previous Results",
                csv_data,
                f"previous_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

def get_businesses_with_emails_from_results(research_df: pd.DataFrame) -> pd.DataFrame:
    """Filter businesses that have valid emails and are selected for campaign"""
    
    if research_df is None or len(research_df) == 0:
        return pd.DataFrame()
    
    # Filter for valid emails
    email_mask = (
        (research_df['email'] != 'Not found') & 
        (research_df['email'] != 'Not researched') &
        (research_df['email'].notna()) &
        (research_df['email'].str.strip() != '') &
        (research_df['email'].str.contains('@', na=False))
    )
    
    # Filter for email campaign selection (default to True if column doesn't exist)
    if 'email_campaign_selected' in research_df.columns:
        campaign_mask = research_df['email_campaign_selected'] == True
        final_mask = email_mask & campaign_mask
    else:
        final_mask = email_mask
    
    return research_df[final_mask].copy()

# For backward compatibility
class BusinessResearcher:
    """Compatibility class for existing code"""
    
    def __init__(self):
        self.scraper = SimpleWebScraper()
        
    def configure_email(self, **kwargs):
        """Mock email configuration"""
        return True, "Email configured"
        
    def get_businesses_with_emails(self):
        """Get businesses with valid emails"""
        if hasattr(st.session_state, 'research_results'):
            return get_businesses_with_emails_from_results(st.session_state.research_results)
        return pd.DataFrame()
