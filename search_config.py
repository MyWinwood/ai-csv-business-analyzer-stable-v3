"""
Search Configuration for Business Research
Controls which search layers and sources are enabled for comprehensive business research
"""

# Search Layer Configuration
SEARCH_LAYERS_CONFIG = {
    # Layer 1: General business search (always enabled)
    'enable_general_search': True,
    
    # Layer 2: Government and official sources (can be enabled/disabled)
    'enable_government_search': False,  # Set to True to enable government database searches
    
    # Layer 3: Industry-specific sources (can be enabled/disabled)
    'enable_industry_search': False,    # Set to True to enable timber industry specific searches
    
    # Search depth and result limits
    'max_results_per_query': 2,         # Maximum results per individual search query
    'search_depth': 'advanced',         # Tavily search depth: 'basic' or 'advanced'
    'request_delay': 4.0,               # Delay between business research requests (seconds)
}

# Search Quality Configuration
SEARCH_QUALITY_CONFIG = {
    # Enable second verification for ambiguous results
    'enable_second_verification': True,
    
    # Confidence thresholds
    'min_confidence_for_government': 7,  # Minimum confidence for government-verified businesses
    'min_confidence_for_general': 5,     # Minimum confidence for general searches
    
    # Location verification settings
    'strict_location_matching': False,   # Set to True for strict city/address matching
    'allow_nearby_cities': True,         # Allow businesses from nearby cities
}

def get_search_config():
    """Get the current search configuration"""
    return {
        'layers': SEARCH_LAYERS_CONFIG,
        'quality': SEARCH_QUALITY_CONFIG
    }

def get_enabled_layers():
    """Get list of enabled search layers"""
    enabled = []
    if SEARCH_LAYERS_CONFIG.get('enable_general_search', True):
        enabled.append('General Business Search')
    if SEARCH_LAYERS_CONFIG.get('enable_government_search', False):
        enabled.append('Government Sources')
    if SEARCH_LAYERS_CONFIG.get('enable_industry_search', False):
        enabled.append('Industry Sources')
    return enabled

def get_search_summary():
    """Get a summary of current search configuration"""
    enabled_layers = get_enabled_layers()
    return f"Enabled: {', '.join(enabled_layers)} | Depth: {SEARCH_LAYERS_CONFIG.get('search_depth', 'advanced')} | Results: {SEARCH_LAYERS_CONFIG.get('max_results_per_query', 2)} per query"

def enable_government_search():
    """Enable government database searches"""
    SEARCH_LAYERS_CONFIG['enable_government_search'] = True
    print("✅ Government database searches enabled")

def enable_industry_search():
    """Enable industry-specific searches"""
    SEARCH_LAYERS_CONFIG['enable_industry_search'] = True
    print("✅ Industry-specific searches enabled")

def disable_government_search():
    """Disable government database searches"""
    SEARCH_LAYERS_CONFIG['enable_government_search'] = False
    print("❌ Government database searches disabled")

def disable_industry_search():
    """Disable industry-specific searches"""
    SEARCH_LAYERS_CONFIG['enable_industry_search'] = False
    print("❌ Industry-specific searches disabled")

def set_search_depth(depth='advanced'):
    """Set search depth: 'basic' or 'advanced'"""
    if depth in ['basic', 'advanced']:
        SEARCH_LAYERS_CONFIG['search_depth'] = depth
        print(f"✅ Search depth set to: {depth}")
    else:
        print("❌ Invalid search depth. Use 'basic' or 'advanced'")

def set_results_per_query(count=2):
    """Set maximum results per individual search query"""
    if 1 <= count <= 5:
        SEARCH_LAYERS_CONFIG['max_results_per_query'] = count
        print(f"✅ Results per query set to: {count}")
    else:
        print("❌ Results per query must be between 1 and 5")

def enable_comprehensive_search():
    """Enable all search layers for comprehensive research"""
    enable_government_search()
    enable_industry_search() 
    set_search_depth('advanced')
    print("🔍 Comprehensive search mode enabled (Government + Industry + Advanced depth)")

def enable_basic_search():
    """Enable only basic search layers"""
    disable_government_search()
    disable_industry_search()
    set_search_depth('basic')
    print("🔍 Basic search mode enabled (General search only)")

if __name__ == "__main__":
    print("Current Search Configuration:")
    print(f"Summary: {get_search_summary()}")
    print(f"Enabled Layers: {get_enabled_layers()}")
