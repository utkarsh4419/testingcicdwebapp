"""
Authentication service for LogicMonitor API
"""

import hashlib
import base64
import time
import hmac
import logging

from config.keyvault import get_CONFIG
from utils.helpers import return_error

logger = logging.getLogger(__name__)


def generate_auth_header(http_verb, resource_path, data=''):
    """Generate LMv1 authentication header for LogicMonitor API"""
    try:
        CONFIG = get_CONFIG()
        timestamp = str(int(time.time() * 1000))
        string_to_sign = http_verb + timestamp + data + resource_path

        hmac1 = hmac.new(
            CONFIG['access_key'].encode(),
            msg=string_to_sign.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        signature = base64.b64encode(hmac1.encode())
        return f"LMv1 {CONFIG['access_id']}:{signature.decode()}:{timestamp}"

    except Exception as e:
        logger.error(f"Error generating auth header: {str(e)}")
        return return_error(500, f"Error generating authentication header: {str(e)}")
