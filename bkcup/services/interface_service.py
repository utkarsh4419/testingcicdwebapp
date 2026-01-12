"""
Interface-related service functions for LogicMonitor API
"""

import logging
import requests

from config.settings import LM_BASE_URL, DEFAULT_PAGE_SIZE, TARGET_DATASOURCES
from .auth_service import generate_auth_header
from .device_service import search_device_by_name, get_device_datasources
from utils.helpers import return_error, matches_interface_keywords, get_proxies

logger = logging.getLogger(__name__)


def get_interfaces(device_id, devicedatasource_id, proxy=None):
    """Get all active interface instances for a device datasource"""
    all_instances = []
    offset = 0
    size = DEFAULT_PAGE_SIZE

    proxies = get_proxies(proxy)

    while True:
        resource_path = f"/device/devices/{device_id}/devicedatasources/{devicedatasource_id}/instances"
        url = f"{LM_BASE_URL}{resource_path}?offset={offset}&size={size}"

        headers = {
            'Authorization': generate_auth_header('GET', resource_path),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, proxies=proxies, verify=False)
            response.raise_for_status()
            items = response.json().get('data', {}).get('items', [])

        except Exception as e:
            logger.error(f"Error fetching interfaces: {str(e)}")
            return return_error(400, f"Error fetching interfaces: {str(e)}")

        if not items:
            break

        # Filter only active interfaces
        active = [inst for inst in items if inst.get("stopMonitoring") == False]
        all_instances.extend(active)

        offset += size

    return all_instances


def fetch_interfaces_for_device(device_name, proxy=None):
    """Fetch all interfaces for a device matching target datasources"""
    
    # Search for device
    devices = search_device_by_name(device_name, proxy)

    if isinstance(devices, dict) and "status" in devices:
        return devices

    if not devices:
        return return_error(404, f"No device found with name '{device_name}'")

    if len(devices) > 1:
        return return_error(400, f"Multiple devices found with name '{device_name}'")

    selected_device = devices[0]
    device_id = selected_device['id']
    device_display_name = selected_device['name']

    # Get datasources
    datasources = get_device_datasources(device_id, proxy)

    if isinstance(datasources, dict) and "status" in datasources:
        return datasources

    # Filter to target datasources
    filtered_ds = [ds for ds in datasources if ds.get('dataSourceName') in TARGET_DATASOURCES]

    if not filtered_ds:
        return return_error(404, f"No matching datasources found for device '{device_display_name}'")

    result = {
        "status": 200,
        "deviceId": device_id,
        "deviceName": device_display_name,
        "datasources": []
    }

    # Get interfaces for each datasource
    for ds in filtered_ds:
        ds_id = ds['id']
        ds_name = ds['dataSourceName']

        instances = get_interfaces(device_id, ds_id, proxy)

        if isinstance(instances, dict) and "status" in instances:
            return instances

        interfaces = []
        for inst in instances:
            if not inst.get("id") or not inst.get("displayName"):
                continue
            
            display_name = inst.get("displayName")
            description = inst.get("description") or inst.get("ifDescr") or inst.get("ifAlias")
            
            if matches_interface_keywords(display_name):
                interfaces.append({
                    "id": inst.get("id"),
                    "displayName": display_name,
                    "description": description
                })

        result["datasources"].append({
            "dsId": ds_id,
            "dsName": ds_name,
            "interfaces": interfaces,
            "totalMatched": len(interfaces)
        })

    return result
