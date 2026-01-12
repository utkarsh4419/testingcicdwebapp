"""
Application configuration and constants
"""

# Azure Key Vault Configuration
KEY_VAULT_NAME = "secretmanagement1"
KEY_VAULT_URL = "https://secretmanagement1.vault.azure.net/"

# Secret names in Key Vault
SECRET_NAMES = {
    'access_id': 'LM-access-id',
    'access_key': 'LM-access-key'
}

# LogicMonitor API Base URL
LM_BASE_URL = "https://genpact.logicmonitor.com/santaba/rest"

# Keywords to filter interfaces (case-insensitive)
INTERFACE_KEYWORDS = [
    'Gig',
    'Ethernet',
    'Port-channel',
    'Serial',
    'T1',
    'StackSub',
    'StackPort',
    'tunnel',
    'ae',
    'interface'
]

# Target datasources for interfaces
TARGET_DATASOURCES = [
    "SNMP_Network_Interfaces_acc_sw",
    "SNMP_Network_Interfaces"
]

# CDP Datasources for neighbors
CDP_DATASOURCES = ["CDP_Neighbors"]

# Pagination settings
DEFAULT_PAGE_SIZE = 1000

# SDT (Scheduled Down Time) Configuration
SDT_TYPE_ONE_TIME = 1