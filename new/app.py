
from flask import Flask, request, jsonify
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Import configurations
from config.settings import KEY_VAULT_URL, KEY_VAULT_NAME, SECRET_NAMES
from config.keyvault import get_config

# Import services
from services.interface_service import fetch_interfaces_for_device
from services.neighbor_service import fetch_neighbors_for_device
from services.sdt_service import create_alert_suppression, create_bulk_alert_suppression

# ==================== HEALTH CHECK ====================

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "LogicMonitor API Service is running",
        "endpoints": [
            "/api/Lm_Device_Interfaces",
            "/api/Lm_Get_Neighbors",
            "/api/refresh-secrets",
            "/api/test-secrets"
        ]
    })


# ==================== SECRET MANAGEMENT ====================

@app.route('/api/test-secrets', methods=['GET'])
def test_secrets():
    """
    Test endpoint to verify secrets are being retrieved from Azure Key Vault.
    Returns masked credentials for security.
    """
    try:
        config = get_config()
        masked_secrets = config.get_masked_secrets()
        
        all_config = config.get_all()
        secrets_status = {}
        
        for key in SECRET_NAMES.keys():
            value = all_config.get(key)
            if value and len(value) > 0:
                secrets_status[key] = {
                    "status": "loaded",
                    "masked_value": masked_secrets.get(key),
                    "length": len(value)
                }
            else:
                secrets_status[key] = {
                    "status": "NOT LOADED or EMPTY",
                    "masked_value": None,
                    "length": 0
                }
        
        return jsonify({
            "status": 200,
            "message": "Secrets retrieved from Azure Key Vault",
            "key_vault_url": KEY_VAULT_URL,
            "key_vault_name": KEY_VAULT_NAME,
            "secrets": secrets_status,
            "secret_names_in_vault": SECRET_NAMES,
            "authentication_method": "System-Assigned Managed Identity"
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing secrets: {str(e)}")
        return jsonify({
            "status": 500,
            "message": f"Error retrieving secrets from Key Vault: {str(e)}",
            "key_vault_url": KEY_VAULT_URL,
            "key_vault_name": KEY_VAULT_NAME,
            "hint": "Ensure System-Assigned Managed Identity is enabled and has 'Get' and 'List' permissions on Key Vault secrets"
        }), 500



# ==================== DEVICE INTERFACES ====================

@app.route('/api/Lm_Device_Interfaces', methods=['GET', 'POST'])
def lm_device_interfaces():
    """Get device interfaces from LogicMonitor"""
    try:
        device_name = None
        proxy = None

        # Get parameters from query string
        if request.method == 'GET':
            device_name = request.args.get("device")
            proxy = request.args.get("proxy")
        
        # Get parameters from JSON body if not in query string
        if not device_name:
            try:
                body = request.get_json(silent=True)
                if body:
                    device_name = body.get("device")
                    proxy = proxy or body.get("proxy")
            except:
                pass

        # Validate required parameter
        if not device_name:
            return jsonify({
                "status": 400, 
                "message": "Missing 'device' parameter"
            }), 400

        # Call service function
        result = fetch_interfaces_for_device(device_name, proxy)

        status_code = 200 if result.get("status") == 200 else result.get("status", 500)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in Lm_Device_Interfaces: {str(e)}")
        return jsonify({
            "status": 500, 
            "message": str(e)
        }), 500


# ==================== NEIGHBOR INFORMATION ====================

@app.route('/api/Lm_Get_Neighbors', methods=['GET', 'POST'])
def lm_get_neighbors():
    """Get neighbor information for a device interface"""
    try:
        device_id = None
        interface_name = None
        proxy = None

        # Get parameters from query string
        if request.method == 'GET':
            device_id = request.args.get("device_id")
            interface_name = request.args.get("interface_name")
            proxy = request.args.get("proxy")

        # Get parameters from JSON body if not in query string
        if not device_id or not interface_name:
            try:
                body = request.get_json(silent=True)
                if body:
                    device_id = device_id or body.get("device_id")
                    interface_name = interface_name or body.get("interface_name")
                    proxy = proxy or body.get("proxy")
            except:
                pass

        # Validate required parameters
        if not device_id:
            return jsonify({
                "status": 400, 
                "message": "Missing required parameter: 'device_id'"
            }), 400

        if not interface_name:
            return jsonify({
                "status": 400, 
                "message": "Missing required parameter: 'interface_name'"
            }), 400

        logger.info(f"Getting neighbors for device_id: {device_id}, interface: {interface_name}")

        # Call service function
        result = fetch_neighbors_for_device(device_id, interface_name, proxy)

        # Determine HTTP status code
        status_code = result.get("status", 500)
        if status_code == 200:
            http_status = 200
        elif isinstance(status_code, int):
            http_status = status_code
        else:
            http_status = 200 if result.get("status") == "success" else 500

        return jsonify(result), http_status

    except Exception as e:
        logger.error(f"Error in Lm_Get_Neighbors: {str(e)}")
        return jsonify({
            "status": 500, 
            "message": str(e)
        }), 500

# ==================== ALERT SUPPRESSION (SDT) ====================

@app.route('/api/Lm_Alert_Suppression', methods=['POST'])
def lm_alert_suppression():
    """
    Create alert suppression (SDT) for a device interface.
    
    Request Body (JSON):
    {
        "interface_id": "12345",           # Required: Interface/Instance ID
        "interface_name": "GigabitEth0/1", # Required: Interface name (for comment)
        "start_time": "2024-01-15 10:00",  # Required: Start time (YYYY-MM-DD HH:MM)
        "end_time": "2024-01-15 12:00",    # Required: End time (YYYY-MM-DD HH:MM)
        "proxy": ""                         # Optional: Proxy URL
    }
    
    Response (JSON) - Same format as runbook for Logic App compatibility:
    Success:
    {
        "status": "success",
        "message": "SDT created successfully",
        "sdt_id": "SDT_123456",
        "full_response": { ... }
    }
    
    Error:
    {
        "status": "error",
        "message": "Error description",
        "details": "Additional details"
    }
    """
    try:
        # Get parameters from JSON body
        body = request.get_json(silent=True)
        
        if not body:
            return jsonify({
                "status": "error",
                "message": "Missing JSON body",
                "details": "Request must include a JSON body with required parameters"
            }), 400
        
        interface_id = body.get("interface_id")
        interface_name = body.get("interface_name")
        start_time = body.get("start_time")
        end_time = body.get("end_time")
        proxy = body.get("proxy", "")
        
        # Validate required parameters
        missing_params = []
        if not interface_id:
            missing_params.append("interface_id")
        if not interface_name:
            missing_params.append("interface_name")
        if not start_time:
            missing_params.append("start_time")
        if not end_time:
            missing_params.append("end_time")
        
        if missing_params:
            return jsonify({
                "status": "error",
                "message": f"Missing required parameters: {', '.join(missing_params)}",
                "details": {
                    "expected": ["interface_id", "interface_name", "start_time", "end_time"],
                    "missing": missing_params
                }
            }), 400
        
        logger.info(f"Creating alert suppression for interface {interface_name} (ID: {interface_id})")
        logger.info(f"Time range: {start_time} to {end_time}")
        
        # Convert proxy empty string to None
        proxy = proxy if proxy else None
        
        # Call service function
        result = create_alert_suppression(
            interface_id=interface_id,
            interface_name=interface_name,
            start_time_str=start_time,
            end_time_str=end_time,
            proxy=proxy
        )
        
        # Determine HTTP status code based on result
        if result.get("status") == "success":
            http_status = 200
        else:
            http_status = 400
        
        return jsonify(result), http_status
    
    except Exception as e:
        logger.error(f"Error in Lm_Alert_Suppression: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": "Unexpected error occurred"
        }), 500


@app.route('/api/Lm_Bulk_Alert_Suppression', methods=['POST'])
def lm_bulk_alert_suppression():
    """
    Create alert suppression (SDT) for multiple device interfaces.
    
    Request Body (JSON):
    {
        "suppressions": [
            {
                "interface_id": "12345",
                "interface_name": "GigabitEth0/1",
                "start_time": "2024-01-15 10:00",
                "end_time": "2024-01-15 12:00"
            },
            {
                "interface_id": "12346",
                "interface_name": "GigabitEth0/2",
                "start_time": "2024-01-15 10:00",
                "end_time": "2024-01-15 12:00"
            }
        ],
        "proxy": ""  # Optional: Proxy URL (applies to all)
    }
    
    Response (JSON):
    {
        "status": "success" | "partial" | "error",
        "message": "Processed X suppressions: Y succeeded, Z failed",
        "total": X,
        "success_count": Y,
        "error_count": Z,
        "results": [
            {
                "index": 0,
                "interface_id": "12345",
                "interface_name": "GigabitEth0/1",
                "status": "success",
                "message": "SDT created successfully",
                "sdt_id": "SDT_123456"
            },
            ...
        ]
    }
    """
    try:
        # Get parameters from JSON body
        body = request.get_json(silent=True)
        
        if not body:
            return jsonify({
                "status": "error",
                "message": "Missing JSON body",
                "details": "Request must include a JSON body with 'suppressions' array"
            }), 400
        
        suppressions = body.get("suppressions")
        proxy = body.get("proxy", "")
        
        # Validate suppressions array
        if not suppressions:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter: 'suppressions'",
                "details": "Request must include 'suppressions' array with at least one item"
            }), 400
        
        if not isinstance(suppressions, list):
            return jsonify({
                "status": "error",
                "message": "Invalid 'suppressions' parameter",
                "details": "'suppressions' must be an array"
            }), 400
        
        if len(suppressions) == 0:
            return jsonify({
                "status": "error",
                "message": "Empty 'suppressions' array",
                "details": "'suppressions' array must contain at least one item"
            }), 400
        
        logger.info(f"Creating bulk alert suppression for {len(suppressions)} interfaces")
        
        # Convert proxy empty string to None
        proxy = proxy if proxy else None
        
        # Call service function
        result = create_bulk_alert_suppression(
            suppressions=suppressions,
            proxy=proxy
        )
        
        # Determine HTTP status code based on result
        if result.get("status") == "success":
            http_status = 200
        elif result.get("status") == "partial":
            http_status = 207  # Multi-Status
        else:
            http_status = 400
        
        return jsonify(result), http_status
    
    except Exception as e:
        logger.error(f"Error in Lm_Bulk_Alert_Suppression: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": "Unexpected error occurred"
        }), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    app.run()




