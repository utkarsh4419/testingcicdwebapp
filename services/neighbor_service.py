
"""
Neighbor-related service functions for LogicMonitor API
"""

import logging

from config.settings import TARGET_DATASOURCES, CDP_DATASOURCES
from .device_service import search_device_by_name, get_device_datasources
from .interface_service import get_interfaces
from utils.helpers import return_error, extract_auto_property, interface_matches

logger = logging.getLogger(__name__)


def get_neighbor_interface_id(neighbor_device_name, neighbor_interface_name, proxy=None):
    """Find the interface ID for a neighbor device's interface"""
    
    devices = search_device_by_name(neighbor_device_name, proxy)
    
    if isinstance(devices, dict) and "status" in devices:
        return devices
    
    # Try hostname without domain if not found
    if not devices and '.' in neighbor_device_name:
        hostname = neighbor_device_name.split('.')[0]
        devices = search_device_by_name(hostname, proxy)
        
        if isinstance(devices, dict) and "status" in devices:
            return devices
    
    if not devices:
        return {
            "status": "not_found",
            "message": f"Neighbor device '{neighbor_device_name}' not found in LogicMonitor"
        }
    
    neighbor_device = devices[0]
    neighbor_device_id = neighbor_device.get('id')
    neighbor_device_display_name = neighbor_device.get('name')
    
    logger.info(f"Found neighbor device: {neighbor_device_display_name} (ID: {neighbor_device_id})")
    
    # Get datasources
    all_datasources = get_device_datasources(neighbor_device_id, proxy)
    
    if isinstance(all_datasources, dict) and "status" in all_datasources:
        return all_datasources
    
    filtered_ds = [ds for ds in all_datasources if ds.get('dataSourceName') in TARGET_DATASOURCES]
    
    if not filtered_ds:
        return {
            "status": "not_found",
            "message": f"No interface datasources found on neighbor device '{neighbor_device_display_name}'"
        }
    
    # Search for matching interface
    for ds in filtered_ds:
        ds_id = ds['id']
        ds_name = ds['dataSourceName']
        
        logger.info(f"Searching in datasource: {ds_name} (ID: {ds_id})")
        
        instances = get_interfaces(neighbor_device_id, ds_id, proxy)
        
        if isinstance(instances, dict) and "status" in instances:
            return instances
        
        for inst in instances:
            instance_name = inst.get('name', '')
            instance_display_name = inst.get('displayName', '')
            instance_id = inst.get('id')
            
            if interface_matches(neighbor_interface_name, instance_name) or \
               interface_matches(neighbor_interface_name, instance_display_name):
                
                return {
                    "status": "found",
                    "neighbor_device_id": neighbor_device_id,
                    "neighbor_device_name": neighbor_device_display_name,
                    "neighbor_interface_id": instance_id,
                    "neighbor_interface_name": instance_name,
                    "neighbor_interface_display_name": instance_display_name,
                    "datasource_name": ds_name,
                    "datasource_id": ds_id
                }
    
    return {
        "status": "not_found",
        "message": f"Interface '{neighbor_interface_name}' not found on neighbor device '{neighbor_device_display_name}'"
    }


def fetch_neighbors_for_device(device_id, interface_name, proxy=None):
    """Fetch CDP neighbor information for a specific device interface"""
    try:
        # Get device datasources
        all_datasources = get_device_datasources(device_id, proxy)
        
        if isinstance(all_datasources, dict) and "status" in all_datasources:
            return all_datasources
        
        # Filter to CDP datasources
        filtered_ds = [ds for ds in all_datasources if ds.get('dataSourceName') in CDP_DATASOURCES]
        
        if not filtered_ds:
            return return_error(404, "CDP_Neighbors datasource not found for this device")
        
        ds_info = filtered_ds[0]
        ds_id = ds_info['id']

        # Get CDP neighbor instances
        neighbors_instances = get_interfaces(device_id, ds_id, proxy)
        
        if isinstance(neighbors_instances, dict) and "status" in neighbors_instances:
            return neighbors_instances
        
        matched_neighbors = []
        
        for inst in neighbors_instances:
            auto_props = inst.get('autoProperties', [])
            
            local_interface = extract_auto_property(auto_props, 'auto.cdpinterfacename')
            
            if interface_matches(local_interface, interface_name):
                clean_name = extract_auto_property(auto_props, 'auto.cdpcachedeviceid')
                neighbor_device = clean_name.replace(".genpact.com", "") if clean_name else None
                neighbor_interface = extract_auto_property(auto_props, 'auto.cdpcachedeviceport')
                
                logger.info(f"Found CDP neighbor - Local: {local_interface}, "
                          f"Neighbor Device: {neighbor_device}, Neighbor Interface: {neighbor_interface}")
                
                # Get neighbor interface details
                neighbor_interface_info = get_neighbor_interface_id(
                    neighbor_device, 
                    neighbor_interface, 
                    proxy
                )
                
                neighbor_data = {
                    "local_interface": local_interface,
                    "neighbor_device_name": neighbor_device,
                    "neighbor_interface_name": neighbor_interface
                }
                
                if neighbor_interface_info.get('status') == 'found':
                    neighbor_data.update({
                        "neighbor_device_id": neighbor_interface_info.get('neighbor_device_id'),
                        "neighbor_interface_id": neighbor_interface_info.get('neighbor_interface_id'),
                        "neighbor_interface_display_name": neighbor_interface_info.get('neighbor_interface_display_name'),
                        "datasource_name": neighbor_interface_info.get('datasource_name'),
                        "datasource_id": neighbor_interface_info.get('datasource_id')
                    })
                else:
                    neighbor_data.update({
                        "neighbor_device_id": None,
                        "neighbor_interface_id": None,
                        "lookup_message": neighbor_interface_info.get('message')
                    })
                
                matched_neighbors.append(neighbor_data)
        
        return {
            "status": 200,
            "device_id": device_id,
            "interface_name": interface_name,
            "neighbors_found": len(matched_neighbors),
            "neighbor_details": matched_neighbors
        }

    except Exception as e:
        logger.error(f"Error fetching neighbors: {str(e)}")
        return return_error(500, f"Unexpected error: {str(e)}")
