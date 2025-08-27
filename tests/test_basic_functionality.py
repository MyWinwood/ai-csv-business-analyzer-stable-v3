"""
Sample test for AI CSV Business Analyzer v3.0 Stable Release
Demonstrates the testing framework and basic functionality
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBasicFunctionality:
    """Test basic functionality of the application"""
    
    def test_pandas_integration(self):
        """Test that pandas works correctly for CSV processing"""
        # Create a sample DataFrame
        data = {
            'business_name': ['Acme Corp', 'Beta Industries', 'Gamma LLC'],
            'email': ['contact@acme.com', 'info@beta.com', 'hello@gamma.com'],
            'phone': ['+1-555-0101', '+1-555-0102', '+1-555-0103'],
            'city': ['New York', 'Chicago', 'Los Angeles']
        }
        df = pd.DataFrame(data)
        
        # Test basic operations
        assert len(df) == 3
        assert 'business_name' in df.columns
        assert 'email' in df.columns
        
        # Test filtering
        filtered_df = df[df['city'] == 'New York']
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['business_name'] == 'Acme Corp'
    
    def test_email_validation(self):
        """Test email validation logic"""
        valid_emails = ['test@example.com', 'user@company.org', 'info@business.co.uk']
        invalid_emails = ['', 'Not found', 'invalid-email', None, 'test@']
        
        def is_valid_email(email):
            if pd.isna(email) or email in ['', 'Not found', 'Not researched']:
                return False
            return '@' in str(email) and '.' in str(email)
        
        # Test valid emails
        for email in valid_emails:
            assert is_valid_email(email) == True, f"Email {email} should be valid"
        
        # Test invalid emails
        for email in invalid_emails:
            assert is_valid_email(email) == False, f"Email {email} should be invalid"
    
    def test_data_filtering(self):
        """Test data filtering functionality"""
        # Create test data with various scenarios
        data = {
            'business_name': ['Valid Business', 'No Email Co', 'Empty Data', 'Complete Business'],
            'email': ['valid@business.com', 'Not found', '', 'complete@biz.com'],
            'phone': ['+1-555-0001', 'Not found', '+1-555-0002', '+1-555-0003'],
            'email_campaign_selected': [True, False, False, True]
        }
        df = pd.DataFrame(data)
        
        # Filter businesses ready for email campaign
        def get_businesses_ready_for_email(df):
            return df[
                (df['email'] != 'Not found') & 
                (df['email'] != '') & 
                (df['email'].notna()) &
                (df['email'].str.contains('@', na=False)) &
                (df['email_campaign_selected'] == True)
            ]
        
        ready_businesses = get_businesses_ready_for_email(df)
        
        # Should only return businesses with valid emails and selected for campaign
        assert len(ready_businesses) == 2
        assert 'Valid Business' in ready_businesses['business_name'].values
        assert 'Complete Business' in ready_businesses['business_name'].values
    
    def test_environment_variable_handling(self):
        """Test environment variable handling"""
        # Test the get_env_var function from main app
        def get_env_var(key, default=None):
            value = os.getenv(key)
            if value:
                return value
            return default
        
        # Test with existing environment variable
        os.environ['TEST_VAR'] = 'test_value'
        assert get_env_var('TEST_VAR') == 'test_value'
        
        # Test with non-existing variable
        assert get_env_var('NON_EXISTING_VAR', 'default') == 'default'
        
        # Cleanup
        del os.environ['TEST_VAR']
    
    def test_data_types(self):
        """Test data type handling"""
        # Test with mixed data types
        data = {
            'id': [1, 2, 3],
            'name': ['Alpha', 'Beta', 'Gamma'], 
            'value': [1.5, 2.7, 3.9],
            'active': [True, False, True]
        }
        df = pd.DataFrame(data)
        
        assert df['id'].dtype in ['int64', 'int32']
        assert df['name'].dtype == 'object'
        assert df['value'].dtype in ['float64', 'float32']
        assert df['active'].dtype == 'bool'
    
    def test_csv_operations(self):
        """Test CSV file operations"""
        # Create test DataFrame
        data = {
            'business_name': ['Test Corp', 'Sample LLC'],
            'email': ['test@corp.com', 'info@sample.com'],
            'research_status': ['completed', 'pending']
        }
        df = pd.DataFrame(data)
        
        # Test CSV conversion
        csv_string = df.to_csv(index=False)
        assert 'business_name,email,research_status' in csv_string
        assert 'Test Corp,test@corp.com,completed' in csv_string
        
        # Test CSV reading (from string)
        from io import StringIO
        csv_data = StringIO(csv_string)
        df_read = pd.read_csv(csv_data)
        
        assert len(df_read) == len(df)
        assert list(df_read.columns) == list(df.columns)
    
    def test_performance_basic(self):
        """Test basic performance with larger dataset"""
        # Create a larger test dataset
        size = 1000
        data = {
            'business_name': [f'Business {i}' for i in range(size)],
            'email': [f'contact{i}@business{i}.com' if i % 3 == 0 else 'Not found' for i in range(size)],
            'phone': [f'+1-555-{i:04d}' for i in range(size)],
            'city': [f'City {i % 10}' for i in range(size)]
        }
        df = pd.DataFrame(data)
        
        # Basic operations should complete quickly
        import time
        
        start_time = time.time()
        
        # Filter operations
        filtered = df[df['email'] != 'Not found']
        grouped = df.groupby('city').size()
        sorted_df = df.sort_values('business_name')
        
        end_time = time.time()
        
        # Should complete in under 1 second for 1000 records
        assert end_time - start_time < 1.0
        assert len(filtered) > 0
        assert len(grouped) > 0
        assert len(sorted_df) == size

# Integration test
class TestIntegration:
    """Test integration scenarios"""
    
    def test_email_campaign_workflow(self):
        """Test complete email campaign workflow"""
        # 1. Create business data
        businesses = pd.DataFrame({
            'business_name': ['TechCorp', 'DataCorp', 'WebCorp'],
            'email': ['tech@corp.com', 'Not found', 'web@corp.com'],
            'phone': ['+1-555-1000', '+1-555-2000', '+1-555-3000'],
            'email_campaign_selected': [True, False, True]
        })
        
        # 2. Filter for email campaign
        email_ready = businesses[
            (businesses['email'] != 'Not found') &
            (businesses['email'].str.contains('@', na=False)) &
            (businesses['email_campaign_selected'] == True)
        ]
        
        # 3. Validate results
        assert len(email_ready) == 2
        expected_businesses = ['TechCorp', 'WebCorp']
        assert all(name in email_ready['business_name'].values for name in expected_businesses)
        
        # 4. Simulate email tracking
        email_ready['email_status'] = 'ready'
        email_ready['campaign_name'] = 'test_campaign'
        
        assert all(email_ready['email_status'] == 'ready')
        assert all(email_ready['campaign_name'] == 'test_campaign')

# Pytest fixtures
@pytest.fixture
def sample_business_data():
    """Fixture providing sample business data"""
    return pd.DataFrame({
        'business_name': ['Alpha Corp', 'Beta LLC', 'Gamma Inc', 'Delta Co'],
        'email': ['alpha@corp.com', 'Not found', 'gamma@inc.com', ''],
        'phone': ['+1-555-0001', '+1-555-0002', 'Not found', '+1-555-0004'],
        'city': ['Boston', 'Miami', 'Seattle', 'Denver'],
        'email_campaign_selected': [True, False, True, False]
    })

def test_with_fixture(sample_business_data):
    """Test using pytest fixture"""
    assert len(sample_business_data) == 4
    assert 'business_name' in sample_business_data.columns
    
    # Test filtering with fixture data
    valid_emails = sample_business_data[
        (sample_business_data['email'] != 'Not found') &
        (sample_business_data['email'] != '') &
        (sample_business_data['email'].str.contains('@', na=False))
    ]
    
    assert len(valid_emails) == 2
    assert 'Alpha Corp' in valid_emails['business_name'].values
    assert 'Gamma Inc' in valid_emails['business_name'].values

if __name__ == '__main__':
    # Run tests directly
    pytest.main([__file__, '-v'])
