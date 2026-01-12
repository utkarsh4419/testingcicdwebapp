"""
SDT (Scheduled Down Time) / Alert Suppression service for LogicMonitor API
"""

import json
import logging
import requests

from config.settings import LM_BASE_URL, SDT_TYPE_ONE_TIME
from .auth_service import generate_auth_header
from utils.helpers import return_error, get_proxies, convert_to_epoch_ms, normalize_time_string

logger = logging.getLogger(__name__)


def create_sdt(instance_id, start_epoch_ms, end_epoch_ms, comment, proxy=None):
    """
    Create a Scheduled Down Time (SDT) for a device datasource instance.
    
    Args:
        instance_id: The datasource instance ID to suppress
        start_epoch_ms: Start time in epoch milliseconds
        end_epoch_ms: End time in epoch milliseconds
        comment: Comment for the SDT
        proxy: Optional proxy URL
    
    Returns:
        dict: Result containing status, message, and SDT details
    """
    resource_path = '/sdt/sdts'
    url = f"{LM_BASE_URL}{resource_path}"
    
    proxies = get_proxies(proxy)
    
    payload = {
        "type": "DeviceDataSourceInstanceSDT",
        "dataSourceInstanceId": instance_id,
        "startDateTime": start_epoch_ms,
        "endDateTime": end_epoch_ms,
        "comment": comment,
        "sdtType": SDT_TYPE_ONE_TIME
    }
    
    headers = {
        'Authorization': generate_auth_header('POST', resource_path, data=json.dumps(payload)),
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            proxies=proxies, 
            json=payload, 
            verify=False
        )
        
        # 1. HTTP error check
        if response.status_code != 200:
            logger.error(f"HTTP Error {response.status_code}: {response.text}")
            return {
                "status": "error",
                "message": f"HTTP Error {response.status_code}",
                "details": response.text
            }
        
        # 2. Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            return {
                "status": "error",
                "message": "Invalid JSON returned from LM API",
                "details": response.text
            }
        
        # 3. Validate LM API status
        if data.get("status") != 200 or data.get("errmsg") != "OK":
            logger.error(f"LM API error: {data}")
            return {
                "status": "error",
                "message": "LM API returned error",
                "details": data
            }
        
        # 4. Ensure SDT ID exists
        sdt_id = data.get("data", {}).get("id")
        if not sdt_id:
            logger.error(f"SDT ID missing in response: {data}")
            return {
                "status": "error",
                "message": "SDT ID missing in LM API response",
                "details": data
            }
        
        # SUCCESS OUTPUT
        logger.info(f"SDT created successfully with ID: {sdt_id}")
        return {
            "status": "success",
            "message": "SDT created successfully",
            "sdt_id": sdt_id,
            "full_response": data
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error creating SDT: {str(e)}")
        return {
            "status": "error",
            "message": f"Request error: {str(e)}",
            "details": "error"
        }
    except Exception as e:
        logger.error(f"Unexpected error creating SDT: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "details": "error"
        }


def create_alert_suppression(interface_id, interface_name, start_time_str, end_time_str, proxy=None):
    """
    Create alert suppression (SDT) for an interface.
    
    Args:
        interface_id: The interface/instance ID to suppress
        interface_name: The interface name (for comment)
        start_time_str: Start time in format 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
        end_time_str: End time in format 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
        proxy: Optional proxy URL
    
    Returns:
        dict: Result containing status, message, and SDT details
    """
    try:
        # Normalize time strings (remove seconds if present)
        start_time_normalized = normalize_time_string(start_time_str)
        end_time_normalized = normalize_time_string(end_time_str)
        
        # Convert user input times to epoch milliseconds
        start_epoch_ms = convert_to_epoch_ms(start_time_normalized)
        end_epoch_ms = convert_to_epoch_ms(end_time_normalized)
        
        logger.info(f"Creating SDT for interface {interface_name} (ID: {interface_id})")
        logger.info(f"Start: {start_time_normalized} ({start_epoch_ms}), End: {end_time_normalized} ({end_epoch_ms})")
        
    except ValueError as e:
        logger.error(f"Time parsing error: {str(e)}")
        return {
            "status": "error",
            "message": f"Invalid time format. Expected 'YYYY-MM-DD HH:MM'. Error: {str(e)}",
            "details": "error"
        }
    except Exception as e:
        logger.error(f"Time conversion error: {str(e)}")
        return {
            "status": "error",
            "message": f"Invalid time format. Expected 'YYYY-MM-DD HH:MM'",
            "details": str(e)
        }
    
    # Create comment for SDT
    comment = f"Suppression via API for {interface_name}"
    
    # Call SDT creation
    result = create_sdt(
        instance_id=interface_id,
        start_epoch_ms=start_epoch_ms,
        end_epoch_ms=end_epoch_ms,
        comment=comment,
        proxy=proxy
    )
    
    return result


def create_bulk_alert_suppression(suppressions, proxy=None):
    """
    Create multiple alert suppressions (SDTs) for multiple interfaces.
    
    Args:
        suppressions: List of dicts with keys: interface_id, interface_name, start_time, end_time
        proxy: Optional proxy URL
    
    Returns:
        dict: Result containing status and results for each suppression
    """
    results = []
    success_count = 0
    error_count = 0
    
    for idx, suppression in enumerate(suppressions):
        interface_id = suppression.get('interface_id')
        interface_name = suppression.get('interface_name', f'Interface_{interface_id}')
        start_time = suppression.get('start_time')
        end_time = suppression.get('end_time')
        
        # Validate required fields
        if not interface_id:
            results.append({
                "index": idx,
                "interface_id": interface_id,
                "status": "error",
                "message": "Missing interface_id"
            })
            error_count += 1
            continue
        
        if not start_time or not end_time:
            results.append({
                "index": idx,
                "interface_id": interface_id,
                "status": "error",
                "message": "Missing start_time or end_time"
            })
            error_count += 1
            continue
        
        # Create suppression
        result = create_alert_suppression(
            interface_id=interface_id,
            interface_name=interface_name,
            start_time_str=start_time,
            end_time_str=end_time,
            proxy=proxy
        )
        
        result["index"] = idx
        result["interface_id"] = interface_id
        result["interface_name"] = interface_name
        
        results.append(result)
        
        if result.get("status") == "success":
            success_count += 1
        else:
            error_count += 1
    
    return {
        "status": "success" if error_count == 0 else ("partial" if success_count > 0 else "error"),
        "message": f"Processed {len(suppressions)} suppressions: {success_count} succeeded, {error_count} failed",
        "total": len(suppressions),
        "success_count": success_count,
        "error_count": error_count,
        "results": results
    }
