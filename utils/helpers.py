"""
Utility helper functions
"""
import logging
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
    """Check if two interface names match (case-insensitive, partial matching)"""
    if not interface1 or not interface2:
        return False
    
    if interface1.lower() == interface2.lower():
        return True
    
    if interface1.lower() in interface2.lower() or interface2.lower() in interface1.lower():
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