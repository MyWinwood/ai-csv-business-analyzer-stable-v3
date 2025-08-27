import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio

# Import web scraping module for business research
try:
    from modules.web_scraping_module import perform_web_scraping
except ImportError:
    perform_web_scraping = None

# Import email configuration
try:
    from email_config import EMAIL_CONFIG
except ImportError:
    EMAIL_CONFIG = None

# Import enhanced business researcher with email integration
try:
    from modules.streamlit_business_researcher import research_businesses_from_dataframe, send_curated_business_emails
    business_research_available = True
except ImportError:
    business_research_available = False

# Import CSV integration functionality
try:
    from modules.csv_research_integrator import CSVResearchIntegrator
    csv_integration_available = True
except ImportError:
    csv_integration_available = False

def get_default_email_templates():
    """Provide default email templates as fallback when emailer is not available"""
    return {
        'business_intro': {
            'subject': 'Business Partnership Opportunity - {your_company_name}',
            'html_body': '''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Hello from {your_company_name}!</h2>
                    
                    <p>Dear {business_name} Team,</p>
                    
                    <p>I hope this message finds you well. My name is {sender_name}, and I represent {your_company_name}.</p>
                    
                    <p>We are interested in exploring potential business opportunities with your organization. Our company specializes in {product_requirements} and we believe there may be synergies between our businesses.</p>
                    
                    <p><strong>What we offer:</strong></p>
                    <ul>
                        <li>Quality products and services</li>
                        <li>Competitive pricing</li>
                        <li>Reliable delivery timelines</li>
                        <li>Professional business relationships</li>
                    </ul>
                    
                    <p>Would you be interested in discussing potential collaboration opportunities? I would be happy to schedule a call at your convenience.</p>
                    
                    <p>Best regards,<br>
                    {sender_name}<br>
                    {your_company_name}<br>
                    Email: {your_email}<br>
                    Phone: {your_phone}</p>
                </div>
            </body>
            </html>
            ''',
            'text_body': 'Hello from {your_company_name}! We are interested in exploring business opportunities with {business_name}.'
        }
    }

def create_data_explorer(df, identifier_cols=None):
    """Simple Data Explorer with Primary and Secondary filters"""
    
    st.title("📊 Data Explorer")

    if df is None or len(df) == 0:
        st.warning("No data available to explore.")
        return
    
    # Get categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if identifier_cols:
        categorical_cols.extend([col for col in identifier_cols if col not in categorical_cols])
    
    categorical_cols = sorted(list(set(categorical_cols)))
    
    if not categorical_cols:
        st.info("No categorical columns found for filtering.")
        st.dataframe(df.head(100), use_container_width=True)
        return
    
    # Filter section
    st.subheader("🔍 Filter Your Data:")
    
    col1, col2 = st.columns(2)
    
    # PRIMARY FILTER
    with col1:
        st.write("**Primary Filter**")
        primary_filter_col = st.selectbox(
            "Select Column",
            ["None"] + categorical_cols,
            key="new_primary_col"
        )
        
        if primary_filter_col != "None":
            unique_values = ["All"] + sorted([str(val) for val in df[primary_filter_col].dropna().unique()])
            primary_filter_value = st.selectbox(
                f"Filter by {primary_filter_col}",
                unique_values,
                key="new_primary_val"
            )
            
            primary_search = st.text_input(
                f"Search in {primary_filter_col}",
                placeholder="Enter search term...",
                key="new_primary_search"
            )
        else:
            primary_filter_value = "All"
            primary_search = ""
    
    # SECONDARY FILTER  
    with col2:
        st.write("**Secondary Filter**")
        secondary_options = [col for col in categorical_cols if col != primary_filter_col]
        
        secondary_filter_col = st.selectbox(
            "Select Column",
            ["None"] + secondary_options,
            key="new_secondary_col"
        )
        
        if secondary_filter_col != "None":
            unique_values = ["All"] + sorted([str(val) for val in df[secondary_filter_col].dropna().unique()])
            secondary_filter_value = st.selectbox(
                f"Filter by {secondary_filter_col}",
                unique_values,
                key="new_secondary_val"
            )
            
            secondary_search = st.text_input(
                f"Search in {secondary_filter_col}",
                placeholder="Enter search term...",
                key="new_secondary_search"
            )
        else:
            secondary_filter_value = "All"
            secondary_search = ""
    
    # Apply filters
    filtered_df = df.copy()
    
    if primary_filter_col != "None":
        if primary_filter_value != "All":
            filtered_df = filtered_df[filtered_df[primary_filter_col].astype(str) == primary_filter_value]
        
        if primary_search:
            mask = filtered_df[primary_filter_col].astype(str).str.contains(primary_search, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    if secondary_filter_col != "None":
        if secondary_filter_value != "All":
            filtered_df = filtered_df[filtered_df[secondary_filter_col].astype(str) == secondary_filter_value]
        
        if secondary_search:
            mask = filtered_df[secondary_filter_col].astype(str).str.contains(secondary_search, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    # Results summary
    st.markdown("---")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("📊 Records", f"{len(filtered_df):,}")
    with col_m2:
        pct = (len(filtered_df) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("📈 % of Total", f"{pct:.1f}%")
    with col_m3:
        st.metric("🔢 Columns", len(filtered_df.columns))
    with col_m4:
        completeness = (1 - filtered_df.isnull().sum().sum() / (len(filtered_df) * len(filtered_df.columns))) * 100 if len(filtered_df) > 0 else 0
        st.metric("✅ Quality", f"{completeness:.1f}%")
    
    if len(filtered_df) == 0:
        st.warning("No records match your filter criteria.")
        return
    
    # Display options
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        max_rows = min(500, len(filtered_df))
        rows_to_show = st.slider("Rows to display:", 10, max_rows, min(100, max_rows)) if max_rows > 10 else max_rows
    
    with col_d2:
        st.write(f"Showing {min(rows_to_show, len(filtered_df))} of {len(filtered_df)} rows")
    
    # Show data
    st.dataframe(filtered_df.head(rows_to_show), use_container_width=True, height=400)
    
    # Download button
    st.markdown("---")
    if len(filtered_df) > 0:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📊 Download CSV",
            csv,
            f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )