"""
Utility helper functions
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from config.settings import INTERFACE_KEYWORDS

logger = logging.getLogger(__name__)


def return_error(status_code, message):
    """Standard error response format"""
    return {
        "status": status_code,
        "message": message
    }


def matches_interface_keywords(display_name):
    """
    Check if the interface display name contains any of the target keywords.
    Case-insensitive matching.
    """
    if not display_name:
        return False
    
    display_name_lower = display_name.lower()
    
    for keyword in INTERFACE_KEYWORDS:
        if keyword.lower() in display_name_lower:
            return True
    
    return False


def extract_auto_property(auto_properties, property_name):
    """Extract a specific property from auto_properties list"""
    if not auto_properties:
        return None
    
    for prop in auto_properties:
        if prop.get('name') == property_name:
            return prop.get('value')
    
    return None


def interface_matches(interface1, interface2):
    """Check if two interface names match"""
    if not interface1 or not interface2:
        return False
    
    # Normalize both interfaces
    if1_clean = interface1.strip().lower()
    if2_clean = interface2.strip().lower()
    
    # Direct exact match
    if if1_clean == if2_clean:
        return True
    
    # Extract port numbers using regex for numbered interfaces
    
    # Pattern to match interface with port numbers (e.g., "1/2/0/21")
    pattern = r'([a-z]+)([\d/]+)\$'
    
    match1 = re.search(pattern, if1_clean)
    match2 = re.search(pattern, if2_clean)
    
    if match1 and match2:
        type1, port1 = match1.groups()
        type2, port2 = match2.groups()
        
        # Both interface type and full port path must match exactly
        if type1 == type2 and port1 == port2:
            return True
    
    # Partial match only if one ENDS with the same unique identifier
    # Prevent "GigE1/2/0/2" matching "GigE1/2/0/21"
    if if1_clean.endswith('/') or if2_clean.endswith('/'):
        return False
    
    # Check if shorter string is a suffix of longer (for abbreviations)
    # But only if it ends with word boundary
    if len(if1_clean) < len(if2_clean):
        # Check if if1 is abbreviated form of if2
        if if2_clean.endswith(if1_clean) or if1_clean in if2_clean.split():
            return True
    elif len(if2_clean) < len(if1_clean):
        # Check if if2 is abbreviated form of if1
        if if1_clean.endswith(if2_clean) or if2_clean in if1_clean.split():
            return True
    
    return False



def get_proxies(proxy):
    """Get proxy dictionary for requests"""
    return {'http': proxy, 'https': proxy} if proxy else None


def convert_to_epoch_ms(date_str):
    """
    Convert 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM' into epoch milliseconds (IST input)
    
    Args:
        date_str: Date string in format 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
    
    Returns:
        int: Epoch time in milliseconds
    """
    # Try both formats
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    else:
        # If no format matched, try the basic format
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    
    # Define IST as UTC+5:30
    ist = timezone(timedelta(hours=5, minutes=30))
    
    # Attach IST timezone to the datetime
    dt_ist = dt.replace(tzinfo=ist)
    
    # Convert to epoch milliseconds
    return int(dt_ist.timestamp() * 1000)



def normalize_time_string(time_str):
    """
    Normalize time string by removing seconds if present.
    Converts 'YYYY-MM-DD HH:MM:SS' to 'YYYY-MM-DD HH:MM'
    
    Args:
        time_str: Time string to normalize
    
    Returns:
        str: Normalized time string without seconds
    """
    if not time_str:
        return time_str
    
    # If format is 'YYYY-MM-DD HH:MM:SS', remove seconds
    parts = time_str.split(':')
    if len(parts) == 3:
        return ':'.join(parts[:-1])
    
    return time_str