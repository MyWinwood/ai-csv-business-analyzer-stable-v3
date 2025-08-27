import pandas as pd
import streamlit as st
import os
from datetime import datetime
import io

def preprocess_data(df, filename, file_type, target_column="consignee name"):
    """
    Preprocess data by removing duplicates based on target column
    
    Args:
        df: DataFrame to process
        filename: Original filename
        file_type: 'csv' or 'excel'
        target_column: Column name to remove duplicates on (default: "consignee name")
    
    Returns:
        processed_df: DataFrame after preprocessing
        processed_filename: Name of processed file
        processing_summary: Summary of processing steps
    """
    processing_summary = []
    original_rows = len(df)
    
    # Step 1: Convert Excel to CSV conceptually (already loaded as DataFrame)
    if file_type == 'excel':
        processing_summary.append(f"✓ Converted Excel file to CSV format")
    
    # Step 2: Find the target column (case-insensitive search)
    target_col_found = None
    target_col_lower = target_column.lower()
    
    for col in df.columns:
        if col.lower() == target_col_lower or target_col_lower in col.lower():
            target_col_found = col
            break
    
    if target_col_found is None:
        # If exact column not found, look for similar columns
        similar_cols = [col for col in df.columns if any(word in col.lower() for word in ['consignee', 'customer', 'client', 'buyer', 'name'])]
        if similar_cols:
            target_col_found = similar_cols[0]
            processing_summary.append(f"⚠️ '{target_column}' not found. Using '{target_col_found}' instead")
        else:
            # If no similar column found, use first text column
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                target_col_found = text_cols[0]
                processing_summary.append(f"⚠️ '{target_column}' not found. Using '{target_col_found}' instead")
            else:
                processing_summary.append(f"❌ No suitable column found for duplicate removal")
                return df, filename, processing_summary
    
    # Step 3: Remove duplicates
    if target_col_found:
        # Clean the column first - remove extra spaces and handle case
        df[target_col_found] = df[target_col_found].astype(str).str.strip().str.title()
        
        # Remove duplicates keeping first occurrence
        processed_df = df.drop_duplicates(subset=[target_col_found], keep='first')
        duplicates_removed = original_rows - len(processed_df)
        
        processing_summary.append(f"✓ Removed {duplicates_removed} duplicate rows based on '{target_col_found}'")
        processing_summary.append(f"✓ Kept {len(processed_df)} unique rows out of {original_rows} original rows")
    else:
        processed_df = df
    
    # Step 4: Generate processed filename
    base_name = os.path.splitext(filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_filename = f"Preprocessed_{base_name}_{timestamp}.csv"
    
    processing_summary.append(f"✓ Ready to save as: {processed_filename}")
    
    return processed_df, processed_filename, processing_summary

def show_preprocessing_interface(df):
    """Show preprocessing interface"""
    st.subheader("🔧 Data Preprocessing")
    
    if df is None or len(df) == 0:
        st.warning("No data available for preprocessing.")
        return None
    
    # Show current data info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        duplicates = df.duplicated().sum()
        st.metric("Potential Duplicates", duplicates)
    
    # Column selection for duplicate removal
    text_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    if not text_columns:
        st.warning("No text columns available for duplicate removal")
        return df
    
    selected_column = st.selectbox(
        "Select column for duplicate removal:",
        options=text_columns,
        help="Choose the column to identify duplicate rows"
    )
    
    # Preview duplicates
    if st.button("Preview Duplicates"):
        if selected_column:
            duplicate_mask = df.duplicated(subset=[selected_column], keep=False)
            duplicates_df = df[duplicate_mask].sort_values(selected_column)
            
            if len(duplicates_df) > 0:
                st.write(f"Found {len(duplicates_df)} duplicate rows based on '{selected_column}':")
                st.dataframe(duplicates_df.head(20))
            else:
                st.success(f"No duplicates found in column '{selected_column}'")
    
    # Process button
    if st.button("🚀 Remove Duplicates", type="primary"):
        if selected_column:
            original_count = len(df)
            processed_df = df.drop_duplicates(subset=[selected_column], keep='first')
            removed_count = original_count - len(processed_df)
            
            if removed_count > 0:
                st.success(f"✅ Removed {removed_count} duplicate rows. {len(processed_df)} unique rows remaining.")
                
                # Show download option
                csv = processed_df.to_csv(index=False)
                filename = f"preprocessed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                st.download_button(
                    "📥 Download Processed Data",
                    csv,
                    filename,
                    "text/csv"
                )
                
                return processed_df
            else:
                st.info("No duplicates found to remove.")
    
    return df

def show_preprocessing_summary(df):
    """Show preprocessing summary"""
    if df is not None and len(df) > 0:
        st.success("✅ Data preprocessing completed successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Processed Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        
        return True
    return False