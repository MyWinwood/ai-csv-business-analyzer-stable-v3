"""
Enhanced Streamlit Business Researcher with Government Sources and Email Integration
Includes specific searches for government business databases and official registrations
Focused on teak, wood, timber, lumber businesses with city/address verification
Integrated with Business Email Module for curated outreach
"""

import asyncio
import csv
import os
import json
import tempfile
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
from tavily import TavilyClient
from modules.business_emailer import BusinessEmailer, get_email_provider_config
from search_config import SEARCH_LAYERS_CONFIG, get_search_config, get_enabled_layers, get_search_summary

# Load environment variables
load_dotenv()

class StreamlitBusinessResearcher:
    def __init__(self):
        # Load API keys from environment variables (Render will provide these)
        self.tavily_key = os.getenv('TAVILY_API_KEY')
        self.groq_key = os.getenv('GROQ_API_KEY')
        
        # Validate required keys
        if not self.tavily_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables!")
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not found in environment variables!")
        
        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=self.tavily_key)
        
        # Initialize email module
        self.emailer = BusinessEmailer()
        
        self.results = []
    
    def test_apis(self):
        """Test all APIs before starting research"""
        print("Testing APIs...")
        
        # Test Groq
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "Say 'Groq working'"}],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    print("✅ Groq API: Working")
                else:
                    return False, "Groq API: Empty response"
            else:
                error_msg = f"Groq API: HTTP {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                error_msg = f"Groq API: Billing/Quota Issue - {e}"
                print(f"💳 {error_msg}")
                return False, error_msg
            else:
                error_msg = f"Groq API: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        # Test Tavily
        try:
            response = self.tavily_client.search("test query", max_results=1)
            if response.get('results'):
                print("✅ Tavily API: Working")
            else:
                return False, "Tavily API: No results"
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str or "limit" in error_str:
                error_msg = f"Tavily API: Billing/Quota Issue - {e}"
                print(f"💳 {error_msg}")
                return False, error_msg
            else:
                error_msg = f"Tavily API: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        
        return True, "All APIs working"
    
    async def research_business_direct(self, business_name, expected_city=None, expected_address=None):
        """Research business using comprehensive multi-layer strategy"""
        
        print(f"Researching: {business_name}")
        
        try:
            # General business search
            search_results = []
            
            search_queries = [
                f"{business_name} wood timber teak contact information phone email",
                f"{business_name} lumber plywood business address website",
                f"{business_name} timber trading company official contact",
                f"{business_name} wood export import contact details"
            ]
            
            for query in search_queries:
                try:
                    print(f"  Searching: {query[:60]}...")
                    
                    response = self.tavily_client.search(
                        query=query,
                        max_results=2,
                        search_depth="advanced"
                    )
                    
                    if response.get('results'):
                        search_results.extend(response['results'])
                        print(f"    Found {len(response['results'])} results")
                    else:
                        print(f"    No results")
                        
                except Exception as e:
                    print(f"    Error: {str(e)[:50]}")
                    
            if not search_results:
                print(f"No search results found for {business_name}")
                return self.create_manual_fallback(business_name)
            
            # Extract contact info using Groq AI
            contact_info = await self.extract_contacts_with_groq(
                business_name, search_results, expected_city, expected_address
            )
            
            return contact_info
            
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                print(f"API Billing Error for {business_name}: {e}")
                return self.create_billing_error_result(business_name)
            else:
                print(f"Error researching {business_name}: {e}")
                return self.create_manual_fallback(business_name)
    
    async def extract_contacts_with_groq(self, business_name, search_results, expected_city=None, expected_address=None):
        """Enhanced Groq extraction with business data analysis"""
        
        print(f"  Analyzing {len(search_results)} results with Groq...")
        
        # Format results for Groq analysis
        results_text = "\n".join([
            f"RESULT {i+1}:\nTitle: {result.get('title', 'No title')}\nURL: {result.get('url', 'No URL')}\nContent: {result.get('content', 'No content')[:400]}...\n"
            for i, result in enumerate(search_results[:6])
        ])
        
        # Build location context
        location_context = ""
        if expected_city or expected_address:
            location_context = f"""
EXPECTED LOCATION FROM INPUT DATA:
Expected City: {expected_city if expected_city else 'Not provided'}
Expected Address: {expected_address if expected_address else 'Not provided'}

LOCATION VERIFICATION REQUIRED:
You must verify if the business address/city found in search results matches or is relevant to the expected location above.
"""
        
        prompt = f"""You are analyzing search results for businesses related to TEAK, WOOD, TIMBER, LUMBER, and PLYWOOD industries.

BUSINESS TO RESEARCH: "{business_name}"

{location_context}

SEARCH RESULTS:
{results_text}

INSTRUCTIONS:
1. FOCUS: Only analyze if this business is related to teak, wood, timber, lumber, plywood, or wooden products industry
2. LOCATION VERIFICATION: If expected city/address is provided, verify if found business location matches
3. EXTRACT: Complete business information

EXTRACT AND FORMAT:
BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: [YES/NO - Is this business related to wood, timber, teak, lumber, plywood industry?]
LOCATION_RELEVANT: [YES/NO/UNKNOWN - Does the found address match expected city/address?]
PHONE: [extract phone number if found and business is relevant, or "Not found"]
EMAIL: [extract email address if found and business is relevant, or "Not found"]  
WEBSITE: [extract official website URL if found and business is relevant, or "Not found"]
ADDRESS: [extract business address if found and business is relevant, or "Not found"]
CITY: [extract city from address if found, or "Not found"]
DESCRIPTION: [brief description focusing on wood/timber business activities]
CONFIDENCE: [rate 1-10 based on quality and number of sources]
RELEVANCE_NOTES: [explain industry relevance, location match, and source quality]

STRICT RULES:
1. Only extract information if INDUSTRY_RELEVANT = YES
2. Only extract information if LOCATION_RELEVANT = YES or UNKNOWN
3. If business is not wood/timber related, set all contact fields to "Not relevant - not wood/timber business"
4. If location doesn't match expected city/address, set all contact fields to "Not relevant - location mismatch"

Format your response exactly as shown above with the field names.
        """
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1200,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('content'):
                    extracted_info = result['choices'][0]['message']['content']
                    print(f"  ✅ Groq extraction completed")
                    
                    result_data = {
                        'business_name': business_name,
                        'extracted_info': extracted_info,
                        'raw_search_results': search_results,
                        'total_sources': len(search_results),
                        'research_date': datetime.now().isoformat(),
                        'method': 'Tavily + Groq Analysis',
                        'status': 'success',
                        'expected_city': expected_city,
                        'expected_address': expected_address
                    }
                    
                    self.results.append(result_data)
                    
                    # Display results
                    print(f"  Results for {business_name}:")
                    print("-" * 60)
                    print(extracted_info)
                    print("-" * 60)
                    
                    return result_data
                else:
                    print(f"  Groq returned empty response")
                    return self.create_manual_fallback(business_name)
            else:
                print(f"  Groq API error: HTTP {response.status_code} - {response.text}")
                return self.create_manual_fallback(business_name)
                
        except Exception as e:
            error_str = str(e).lower()
            if "billing" in error_str or "quota" in error_str or "insufficient" in error_str:
                print(f"Groq Billing Error: {e}")
                raise Exception(f"Groq API billing issue: {e}")
            else:
                print(f"  Groq extraction error: {e}")
                return self.create_manual_fallback(business_name)
    
    def create_manual_fallback(self, business_name):
        """Create fallback result for manual research"""
        
        fallback_info = f"""
BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: UNKNOWN
LOCATION_RELEVANT: UNKNOWN
PHONE: Research required
EMAIL: Research required
WEBSITE: Research required  
ADDRESS: Research required
CITY: Research required
DESCRIPTION: Business - requires manual verification for wood/timber relevance
CONFIDENCE: 1
RELEVANCE_NOTES: Automated research failed - manual verification needed
        """
        
        result = {
            'business_name': business_name,
            'extracted_info': fallback_info,
            'raw_search_results': [],
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'method': 'Manual Fallback',
            'status': 'manual_required'
        }
        
        self.results.append(result)
        print(f"  Manual research required for {business_name}")
        return result
    
    def create_billing_error_result(self, business_name):
        """Create result for billing error cases"""
        
        billing_info = f"""
BUSINESS_NAME: {business_name}
INDUSTRY_RELEVANT: UNKNOWN
LOCATION_RELEVANT: UNKNOWN
PHONE: API billing error
EMAIL: API billing error
WEBSITE: API billing error  
ADDRESS: API billing error
CITY: API billing error
DESCRIPTION: Research stopped due to API billing/quota issue
CONFIDENCE: 0
RELEVANCE_NOTES: Research was stopped due to API billing or quota limits
        """
        
        result = {
            'business_name': business_name,
            'extracted_info': billing_info,
            'raw_search_results': [],
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'method': 'Billing Error',
            'status': 'billing_error'
        }
        
        self.results.append(result)
        print(f"  Billing error occurred for {business_name}")
        return result
    
    async def research_from_dataframe(self, df, consignee_column='Consignee Name', city_column=None, address_column=None, max_businesses=None, enable_justdial=False):
        """Research businesses from DataFrame"""
        
        # Extract business names from the specified column
        if consignee_column not in df.columns:
            available_cols = [col for col in df.columns if 'consignee' in col.lower() or 'name' in col.lower()]
            if available_cols:
                consignee_column = available_cols[0]
                print(f"Column '{consignee_column}' not found. Using '{consignee_column}' instead.")
            else:
                raise ValueError(f"Column '{consignee_column}' not found in DataFrame. Available columns: {list(df.columns)}")
        
        # Auto-detect city and address columns if not specified
        if not city_column:
            city_cols = [col for col in df.columns if 'city' in col.lower()]
            city_column = city_cols[0] if city_cols else None
            
        if not address_column:
            addr_cols = [col for col in df.columns if 'address' in col.lower()]
            address_column = addr_cols[0] if addr_cols else None
        
        print(f"Using columns - Business: {consignee_column}, City: {city_column}, Address: {address_column}")
        
        # Get unique business names with their city/address info
        business_data = []
        for _, row in df.iterrows():
            business_name = row.get(consignee_column)
            if pd.notna(business_name) and str(business_name).strip():
                city = row.get(city_column) if city_column else None
                address = row.get(address_column) if address_column else None
                business_data.append({
                    'name': str(business_name).strip(),
                    'city': str(city).strip() if pd.notna(city) else None,
                    'address': str(address).strip() if pd.notna(address) else None
                })
        
        # Remove duplicates based on business name
        unique_businesses = {}
        for item in business_data:
            if item['name'] not in unique_businesses:
                unique_businesses[item['name']] = item
        
        business_list = list(unique_businesses.values())
        
        if not business_list:
            raise ValueError(f"No business names found in column '{consignee_column}'")
        
        # Limit number of businesses if specified
        if max_businesses and max_businesses < len(business_list):
            business_list = business_list[:max_businesses]
            print(f"Limited to first {max_businesses} businesses")
        
        total_businesses = len(business_list)
        print(f"Found {total_businesses} unique businesses to research")
        
        # Research each business
        successful = 0
        manual_required = 0
        billing_errors = 0
        
        for i, business_info in enumerate(business_list, 1):
            business_name = business_info['name']
            expected_city = business_info['city']
            expected_address = business_info['address']
            
            print(f"\nProgress: {i}/{total_businesses}")
            print(f"Business: {business_name}")
            if expected_city:
                print(f"Expected City: {expected_city}")
            if expected_address:
                print(f"Expected Address: {expected_address}")
            
            try:
                result = await self.research_business_direct(
                    business_name, expected_city, expected_address
                )
                
                if result['status'] == 'success':
                    successful += 1
                elif result['status'] == 'manual_required':
                    manual_required += 1
                elif result['status'] == 'billing_error':
                    billing_errors += 1
                    print("Stopping research due to billing error.")
                    break
                
                # Add delay between requests
                await asyncio.sleep(3)
                
            except Exception as e:
                error_str = str(e).lower()
                if "billing" in error_str or "quota" in error_str:
                    print(f"BILLING ERROR: {e}")
                    billing_errors += 1
                    break
                else:
                    print(f"Unexpected error: {e}")
                    manual_required += 1
        
        # Return summary
        summary = {
            'total_processed': len(self.results),
            'successful': successful,
            'manual_required': manual_required,
            'billing_errors': billing_errors,
            'success_rate': successful/len(self.results)*100 if self.results else 0
        }
        
        return summary
    
    def get_results_dataframe(self):
        """Convert results to DataFrame"""
        
        if not self.results:
            return pd.DataFrame()
        
        csv_data = []
        for result in self.results:
            csv_row = self.parse_extracted_info_to_csv(result)
            csv_data.append(csv_row)
        
        return pd.DataFrame(csv_data)
    
    def parse_extracted_info_to_csv(self, result):
        """Parse extracted info text into CSV fields"""
        info = result['extracted_info']
        business_name = result['business_name']
        
        csv_row = {
            'business_name': business_name,
            'industry_relevant': self.extract_field_value(info, 'INDUSTRY_RELEVANT:'),
            'location_relevant': self.extract_field_value(info, 'LOCATION_RELEVANT:'),
            'phone': self.extract_field_value(info, 'PHONE:'),
            'email': self.extract_field_value(info, 'EMAIL:'),
            'website': self.extract_field_value(info, 'WEBSITE:'),
            'address': self.extract_field_value(info, 'ADDRESS:'),
            'city': self.extract_field_value(info, 'CITY:'),
            'description': self.extract_field_value(info, 'DESCRIPTION:'),
            'confidence': self.extract_field_value(info, 'CONFIDENCE:'),
            'relevance_notes': self.extract_field_value(info, 'RELEVANCE_NOTES:'),
            'status': result['status'],
            'total_sources': result.get('total_sources', 0),
            'research_date': result['research_date'],
            'method': result['method'],
            'expected_city': result.get('expected_city', ''),
            'expected_address': result.get('expected_address', '')
        }
        
        # Add email campaign selection column
        email = csv_row.get('email', '')
        csv_row['email_campaign_selected'] = bool(
            email and 
            email != 'Not found' and 
            email != 'Research required' and 
            email != 'API billing error' and
            '@' in email
        )
        
        return csv_row
    
    def extract_field_value(self, text, field_name):
        """Extract field value from formatted text"""
        try:
            lines = text.split('\n')
            for line in lines:
                if line.strip().startswith(field_name):
                    value = line.replace(field_name, '').strip()
                    return value if value and value != "Not found" else ""
            return ""
        except:
            return ""
    
    def get_businesses_with_emails(self):
        """Get list of businesses that have email addresses from research results"""
        if not self.results:
            return pd.DataFrame()
        
        results_df = self.get_results_dataframe()
        
        # Filter businesses with valid email addresses
        businesses_with_emails = results_df[
            (results_df['email'].notna()) & 
            (results_df['email'] != '') & 
            (results_df['email'] != 'Not found') &
            (results_df['email'] != 'Research required') &
            (results_df['email'] != 'API billing error') &
            (results_df['email'].str.contains('@', na=False))
        ].copy()
        
        return businesses_with_emails
    
    def configure_email(self, email_provider='gmail', email_address=None, email_password=None, sender_name=None):
        """Configure email settings for sending curated emails"""
        try:
            if not email_address or not email_password:
                return False, "Email address and password are required"
            
            provider_config = get_email_provider_config(email_provider)
            if not provider_config:
                return False, f"Email provider '{email_provider}' not supported"
            
            # Configure SMTP settings
            self.emailer.configure_smtp(
                smtp_server=provider_config['smtp_server'],
                port=provider_config['port'],
                email=email_address,
                password=email_password,
                sender_name=sender_name or email_address
            )
            
            # Test the configuration
            test_success, test_message = self.emailer.test_email_config()
            
            if test_success:
                return True, f"Email configured successfully with {email_provider.title()}"
            else:
                return False, f"Email configuration failed: {test_message}"
                
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"
    
    async def send_curated_emails(self, selected_businesses=None, template_name='business_intro', 
                                email_variables=None, delay_seconds=2.0, 
                                progress_callback=None, status_callback=None):
        """Send curated emails to selected businesses or all businesses with email addresses"""
        
        try:
            # Get businesses with emails
            if selected_businesses is not None:
                businesses_to_email = selected_businesses
            else:
                businesses_to_email = self.get_businesses_with_emails()
            
            if len(businesses_to_email) == 0:
                return {
                    'success': False,
                    'message': 'No businesses with email addresses found',
                    'summary': {
                        'total_businesses': 0,
                        'emails_to_send': 0,
                        'emails_sent': 0,
                        'emails_failed': 0,
                        'success_rate': 0
                    }
                }
            
            # Prepare default email variables if not provided
            if not email_variables:
                email_variables = {
                    'your_company_name': 'Your Company Name',
                    'sender_name': 'Your Name',
                    'your_phone': 'Your Phone Number',
                    'your_email': 'your.email@example.com',
                    'product_requirements': 'High-quality timber and wood products',
                    'volume_requirements': 'To be discussed',
                    'timeline_requirements': 'Flexible',
                    'quality_requirements': 'Premium grade'
                }
            
            # Load email templates if not already loaded
            templates = self.emailer.get_default_templates()
            
            # Send bulk emails
            summary = await self.emailer.send_bulk_emails(
                businesses_df=businesses_to_email,
                template_name=template_name,
                base_variables=email_variables,
                delay_seconds=delay_seconds,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
            
            return {
                'success': True,
                'message': f'Email campaign completed. Sent {summary["emails_sent"]} emails.',
                'summary': summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Email campaign failed: {str(e)}',
                'summary': {
                    'total_businesses': 0,
                    'emails_to_send': 0,
                    'emails_sent': 0,
                    'emails_failed': 0,
                    'success_rate': 0
                }
            }
    
    def save_email_log(self, filename=None):
        """Save email sending log"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_email_log_{timestamp}.json"
        
        return self.emailer.save_email_log(filename)


# Main functions for Streamlit interface
async def research_businesses_from_dataframe(df, consignee_column='Consignee Name', city_column=None, address_column=None, max_businesses=10, enable_justdial=False, filter_info=None):
    """Research wood/timber businesses from a DataFrame"""
    
    try:
        researcher = StreamlitBusinessResearcher()
        
        # Test APIs first
        api_ok, api_message = researcher.test_apis()
        if not api_ok:
            raise Exception(f"API Test Failed: {api_message}")
        
        # Research businesses
        summary = await researcher.research_from_dataframe(
            df, 
            consignee_column=consignee_column,
            city_column=city_column,
            address_column=address_column,
            max_businesses=max_businesses,
            enable_justdial=False
        )
        
        # Get results
        results_df = researcher.get_results_dataframe()
        
        # Generate CSV filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"business_research_results_{timestamp}.csv"
        
        return results_df, summary, csv_filename, researcher
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None


# Email integration functions for Streamlit interface
async def send_curated_business_emails(researcher, selected_businesses=None, email_config=None, template_name='business_intro', email_variables=None, delay_seconds=2.0, progress_callback=None, status_callback=None):
    """Send curated emails to businesses with email addresses"""
    
    try:
        # Configure email if provided
        if email_config:
            success, message = researcher.configure_email(
                email_provider=email_config.get('provider', 'gmail'),
                email_address=email_config.get('email'),
                email_password=email_config.get('password'),
                sender_name=email_config.get('sender_name')
            )
            
            if not success:
                return {
                    'success': False,
                    'message': f"Email configuration failed: {message}",
                    'summary': {
                        'total_businesses': 0,
                        'emails_to_send': 0,
                        'emails_sent': 0,
                        'emails_failed': 0,
                        'success_rate': 0
                    }
                }
        
        # Send emails
        return await researcher.send_curated_emails(
            selected_businesses=selected_businesses,
            template_name=template_name,
            email_variables=email_variables,
            delay_seconds=delay_seconds,
            progress_callback=progress_callback,
            status_callback=status_callback
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Email sending failed: {str(e)}",
            'summary': {
                'total_businesses': 0,
                'emails_to_send': 0,
                'emails_sent': 0,
                'emails_failed': 0,
                'success_rate': 0
            }
        }
