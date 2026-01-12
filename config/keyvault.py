"""
Azure Key Vault configuration management
"""

import logging
from functools import lru_cache
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from .settings import KEY_VAULT_URL, SECRET_NAMES

logger = logging.getLogger(__name__)


class KeyVaultConfig:
    """Class to manage Azure Key Vault secrets - Azure Key Vault ONLY, no fallback"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_secrets()
    
    def _get_credential(self):
        """Get Azure credential - System Assigned Managed Identity"""
        try:
            logger.info("Using System-Assigned Managed Identity via DefaultAzureCredential")
            return DefaultAzureCredential()
        except Exception as e:
            logger.error(f"Error getting credential: {str(e)}")
            raise
    
    def _load_secrets(self):
        """Load secrets from Azure Key Vault ONLY - No fallback to environment variables"""
        try:
            credential = self._get_credential()
            client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
            
            config = {}
            for key, secret_name in SECRET_NAMES.items():
                try:
                    secret = client.get_secret(secret_name)
                    config[key] = secret.value
                    logger.info(f"Successfully loaded secret: {secret_name}")
                except Exception as e:
                    logger.error(f"Error loading secret {secret_name}: {str(e)}")
                    raise Exception(f"Failed to load secret '{secret_name}' from Key Vault: {str(e)}")
            
            logger.info("All secrets successfully loaded from Azure Key Vault")
            return config
            
        except Exception as e:
            logger.error(f"Error connecting to Key Vault: {str(e)}")
            raise Exception(f"Failed to connect to Azure Key Vault: {str(e)}")
    
    def get(self, key):
        """Get a specific config value"""
        return self._config.get(key)
    
    def get_all(self):
        """Get all config values"""
        return self._config.copy()
    
    def refresh(self):
        """Refresh secrets from Key Vault"""
        self._config = self._load_secrets()
        return self._config
    
    def get_masked_secrets(self):
        """Get secrets with masked values for testing/display purposes"""
        masked = {}
        for key, value in self._config.items():
            if value:
                if len(value) > 8:
                    masked[key] = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                else:
                    masked[key] = '*' * len(value)
            else:
                masked[key] = "NOT SET"
        return masked


@lru_cache(maxsize=1)
def get_config():
    """Get cached configuration"""
    return KeyVaultConfig()


def get_CONFIG():
    """Get the CONFIG dictionary"""
    return get_config().get_all()
