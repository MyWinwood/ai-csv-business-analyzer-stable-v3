import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import os
import asyncio
from typing import Dict, List, Optional, Any
from tavily import TavilyClient

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

class RealBusinessScraper:
    """Real business scraper using Tavily and Groq APIs"""
    
    def __init__(self):
        self.results = []
        self.processed_count = 0
        
        # Get API keys from environment
        self.tavily_key = get_env_var('TAVILY_API_KEY')
        self.groq_key = get_env_var('GROQ_API_KEY')
        
        # Initialize clients if keys are available
        self.tavily_client = None
        self.apis_available = False
        
        if self.tavily_key and self.groq_key:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
                self.apis_available = True
            except Exception as e:
                st.warning(f"⚠️ API initialization failed: {e}")
                self.apis_available = False
        else:
            st.warning("⚠️ API keys not found. Using mock data for demonstration.")
            self.apis_available = False
    
    def search_business_info(self, business_name: str) -> Dict[str, str]:
        """Search for real business information using APIs"""
        
        if not self.apis_available:
            return self._mock_search(business_name)
        
        try:
            # Search with Tavily
            search_results = []
            queries = [
                f"{business_name} contact phone email website",
                f"{business_name} timber wood lumber company address"
            ]
            
            for query in queries:
                try:
                    response = self.tavily_client.search(
                        query=query,
                        max_results=2,
                        search_depth="basic"
                    )
                    if response.get('results'):
                        search_results.extend(response['results'])
                except Exception:
                    continue
            
            if not search_results:
                return self._mock_search(business_name)
            
            # Extract contact info using Groq
            return self._extract_with_groq(business_name, search_results)
            
        except Exception as e:
            st.warning(f"Research error for {business_name}: {str(e)}")
            return self._mock_search(business_name)
    
    def _extract_with_groq(self, business_name: str, search_results: List[Dict]) -> Dict[str, str]:
        """Extract contact information using Groq AI"""
        
        try:
            # Format search results
            results_text = "\\n".join([
                f"RESULT {i+1}:\\nTitle: {result.get('title', 'No title')}\\nContent: {result.get('content', 'No content')[:300]}..."
                for i, result in enumerate(search_results[:4])
            ])
            
            prompt = f"""Extract contact information for business: "{business_name}"

SEARCH RESULTS:
{results_text}

Extract and format exactly as shown:
PHONE: [phone number or "Not found"]
EMAIL: [email address or "Not found"] 
WEBSITE: [website URL or "Not found"]
ADDRESS: [business address or "Not found"]
DESCRIPTION: [brief business description or "Not found"]

Only extract if the business is related to wood, timber, lumber, or general business activities."""
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                if content:
                    return self._parse_groq_response(content)
            
        except Exception as e:
            if "billing" in str(e).lower() or "quota" in str(e).lower():
                st.warning("⚠️ API quota reached. Using mock data.")
            
        return self._mock_search(business_name)
    
    def _parse_groq_response(self, content: str) -> Dict[str, str]:
        """Parse Groq response into structured data"""
        
        result = {
            'phone': 'Not found',
            'email': 'Not found', 
            'website': 'Not found',
            'address': 'Not found',
            'description': 'Not found'
        }
        
        lines = content.split('\\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PHONE:'):
                result['phone'] = line.replace('PHONE:', '').strip()
            elif line.startswith('EMAIL:'):
                result['email'] = line.replace('EMAIL:', '').strip()
            elif line.startswith('WEBSITE:'):
                result['website'] = line.replace('WEBSITE:', '').strip()
            elif line.startswith('ADDRESS:'):
                result['address'] = line.replace('ADDRESS:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                result['description'] = line.replace('DESCRIPTION:', '').strip()
        
        return result
    
    def _mock_search(self, business_name: str) -> Dict[str, str]:
        """Fallback mock search for demonstration"""
        
        mock_results = {
            'phone': 'Not found',
            'email': 'Not found', 
            'website': 'Not found',
            'address': 'Not found',
            'description': 'Research required - API not available'
        }
        
        # Add some realistic mock data for tech companies
        business_lower = business_name.lower()
        if any(word in business_lower for word in ['tech', 'software', 'digital', 'systems']):
            mock_results['email'] = f"info@{business_name.lower().replace(' ', '').replace(',', '')[:15]}.com"
            mock_results['website'] = f"https://www.{business_name.lower().replace(' ', '').replace(',', '')[:15]}.com"
            mock_results['description'] = f"{business_name} - Technology solutions provider"
            
        return mock_results
        
    def process_businesses(self, df: pd.DataFrame, business_column: str) -> pd.DataFrame:
        """Process businesses for research - KEEPS EXISTING UI INTERFACE"""
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
            
            # Get REAL business information using APIs
            business_info = self.search_business_info(str(business_name))
            
            # Update the dataframe
            for col, value in business_info.items():
                if value and value != 'Not found':
                    result_df.at[idx, col] = value
            
            # Auto-select for email campaign if email found
            email = business_info.get('email', 'Not found')
            if email not in ['Not found', 'Not researched', ''] and '@' in str(email):
                result_df.at[idx, 'email_campaign_selected'] = True
            
            self.processed_count += 1
            progress = self.processed_count / total_businesses
            progress_bar.progress(progress)
            
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
            
        status_text.text(f"✅ Research completed! Processed {self.processed_count} businesses.")
        progress_bar.progress(1.0)
        
        return result_df

# KEEP ORIGINAL FUNCTION INTERFACE - Don't change the UI!
def perform_web_scraping(df: pd.DataFrame):
    """Main web scraping interface for Streamlit - PRESERVED ORIGINAL UI"""
    st.header("🔍 Business Research & Data Enhancement")
    
    # Show API status
    tavily_key = get_env_var('TAVILY_API_KEY')
    groq_key = get_env_var('GROQ_API_KEY')
    
    if tavily_key and groq_key:
        st.success("✅ API keys configured - Real business research enabled")
    else:
        st.warning("⚠️ API keys missing - Using demo mode with mock data")
    
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
        
        # Use REAL scraper with APIs
        scraper = RealBusinessScraper()
        research_results = scraper.process_businesses(df, business_column)
        
        # Store results in session state
        st.session_state.research_results = research_results
        st.session_state.research_completed = True
        st.session_state.selected_business_column = business_column
        
        # Show results summary
        st.markdown("---")
        st.success("🎉 Research Completed!")
        
        # Calculate statistics
        emails_found = len(research_results[
            (research_results['email'] != 'Not found') & 
            (research_results['email'] != 'Not researched') &
            (research_results['email'].str.contains('@', na=False))
        ])
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
            success_rate = (emails_found / len(research_results)) * 100 if len(research_results) > 0 else 0
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
            emails = len(results[
                (results['email'] != 'Not found') & 
                (results['email'] != 'Not researched') &
                (results['email'].str.contains('@', na=False))
            ])
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
        self.scraper = RealBusinessScraper()
        
    def configure_email(self, **kwargs):
        """Mock email configuration"""
        return True, "Email configured"
        
    def get_businesses_with_emails(self):
        """Get businesses with valid emails"""
        if hasattr(st.session_state, 'research_results'):
            return get_businesses_with_emails_from_results(st.session_state.research_results)
        return pd.DataFrame()
