"""
Device-related service functions for LogicMonitor API
"""

import logging
import requests

from config.settings import LM_BASE_URL, DEFAULT_PAGE_SIZE
from .auth_service import generate_auth_header
from utils.helpers import return_error, get_proxies

logger = logging.getLogger(__name__)


def search_device_by_name(device_name, proxy=None):
    """Search for a device by name in LogicMonitor"""
    resource_path = '/device/devices'
    query_params = f'?filter=displayName:{device_name}&fields=name,id,displayName'
    url = f"{LM_BASE_URL}{resource_path}{query_params}"

    headers = {
        'Authorization': generate_auth_header('GET', resource_path),
        'Content-Type': 'application/json'
    }

    proxies = get_proxies(proxy)

    try:
        response = requests.get(url, headers=headers, proxies=proxies, verify=False)
        response.raise_for_status()
        return response.json().get('data', {}).get('items', [])

    except Exception as e:
        logger.error(f"Error searching device: {str(e)}")
        return return_error(400, f"Error searching device: {str(e)}")


def get_device_datasources(device_id, proxy=None):
    """Get all datasources for a device with pagination"""
    all_ds = []
    offset = 0
    size = DEFAULT_PAGE_SIZE

    proxies = get_proxies(proxy)

    while True:
        resource_path = f"/device/devices/{device_id}/devicedatasources"
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
            logger.error(f"Error fetching datasources: {str(e)}")
            return return_error(400, f"Error fetching datasources: {str(e)}")

        if not items:
            break

        all_ds.extend(items)
        offset += size

    return all_ds
