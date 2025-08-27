import pytest
import pandas as pd
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBasicFunctionality:
    """Test basic application functionality"""
    
    def test_pandas_import(self):
        """Test that pandas is available"""
        assert pd is not None
        
    def test_data_creation(self):
        """Test basic data operations"""
        df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
        assert len(df) == 3
        assert list(df.columns) == ['A', 'B']
        
    def test_data_filtering(self):
        """Test data filtering operations"""
        df = pd.DataFrame({
            'business_name': ['Business A', 'Business B', 'Business C'],
            'email': ['a@test.com', 'Not found', 'c@test.com']
        })
        
        # Filter businesses with valid emails
        valid_emails = df[df['email'] != 'Not found']
        assert len(valid_emails) == 2
        
    def test_streamlit_availability(self):
        """Test that streamlit can be imported"""
        try:
            import streamlit as st
            assert st is not None
        except ImportError:
            pytest.fail("Streamlit not available")
            
if __name__ == '__main__':
    pytest.main([__file__])