import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from src.config import CLEANED_DATA_DIR, GOLD_DATA_DIR

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_blob_service_client(connection_string: Optional[str] = None,
                            account_url: Optional[str] = None,
                            credential: Optional[ClientSecretCredential] = None) -> BlobServiceClient:
    """
    Creates and returns a BlobServiceClient.
    Priority: connection_string > account_url + credential > DefaultAzureCredential (managed identity)
    """
    if connection_string:
        logger.info("Using connection string for Azure Blob Storage authentication.")
        return BlobServiceClient.from_connection_string(connection_string)
    
    if account_url and credential:
        logger.info("Using account URL + client secret credential for Azure Blob Storage authentication.")
        return BlobServiceClient(account_url=account_url, credential=credential)
    
    if account_url:
        logger.info("Using account URL + DefaultAzureCredential for Azure Blob Storage authentication.")
        return BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
    
    raise ValueError(
        "Azure authentication not configured. Provide either:\n"
        "  - AZURE_STORAGE_CONNECTION_STRING\n"
        "  - AZURE_STORAGE_ACCOUNT_URL + AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET\n"
        "  - AZURE_STORAGE_ACCOUNT_URL (for managed identity)"
    )


def upload_file_to_blob(blob_service_client: BlobServiceClient,
                        container_name: str,
                        local_file_path: Path,
                        blob_path: str) -> bool:
    """
    Uploads a single file to Azure Blob Storage.
    Returns True if successful, False otherwise.
    """
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        logger.info(f"Successfully uploaded: {local_file_path.name} -> {blob_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {local_file_path.name}: {str(e)}")
        return False


def upload_directory_to_blob(blob_service_client: BlobServiceClient,
                             container_name: str,
                             local_dir: Path,
                             blob_prefix: str = "") -> dict:
    """
    Uploads all files in a local directory to Azure Blob Storage.
    Preserves directory structure under the blob prefix.
    Returns a summary dict with success/failure counts.
    """
    if not local_dir.exists() or not local_dir.is_dir():
        logger.warning(f"Directory does not exist: {local_dir}")
        return {"uploaded": 0, "failed": 0, "skipped": 0}
    
    summary = {"uploaded": 0, "failed": 0, "skipped": 0}
    
    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            # Calculate relative path from local_dir
            relative_path = file_path.relative_to(local_dir)
            # Construct blob path
            if blob_prefix:
                blob_path = f"{blob_prefix}/{relative_path}"
            else:
                blob_path = str(relative_path)
            
            # Normalize path separators for blob storage (use forward slashes)
            blob_path = blob_path.replace("\\", "/")
            
            success = upload_file_to_blob(blob_service_client, container_name, file_path, blob_path)
            if success:
                summary["uploaded"] += 1
            else:
                summary["failed"] += 1
    
    return summary


def upload_cleaned_data(container_name: str = "airbnb-cleaned-data",
                        connection_string: Optional[str] = None,
                        account_url: Optional[str] = None,
                        credential: Optional[ClientSecretCredential] = None,
                        upload_gold: bool = False) -> dict:
    """
    Main function to upload cleaned (and optionally gold) data to Azure Blob Storage.
    
    Args:
        container_name: Name of the Azure Blob Storage container
        connection_string: Azure Storage connection string (optional, reads from env if not provided)
        account_url: Azure Storage account URL (optional, reads from env if not provided)
        credential: Azure credential object (optional, reads from env if not provided)
        upload_gold: If True, also upload the gold layer (DuckDB DB, reports, plots)
    
    Returns:
        dict with upload summary
    """
    logger.info("=" * 60)
    logger.info("Starting Azure Blob Storage Upload")
    logger.info("=" * 60)
    
    # Read from environment variables if not provided as parameters
    if connection_string is None:
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if account_url is None:
        account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
    if credential is None and account_url and not connection_string:
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        if all([tenant_id, client_id, client_secret]):
            credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    
    # Initialize blob service client
    blob_service_client = get_blob_service_client(connection_string, account_url, credential)
    
    # Ensure container exists
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            logger.info(f"Created container: {container_name}")
        else:
            logger.info(f"Container already exists: {container_name}")
    except Exception as e:
        logger.error(f"Failed to access/create container {container_name}: {str(e)}")
        return {"error": str(e)}
    
    total_summary = {"uploaded": 0, "failed": 0, "skipped": 0}
    
    # Upload cleaned data (Parquet files)
    logger.info(f"Uploading cleaned data from: {CLEANED_DATA_DIR}")
    cleaned_summary = upload_directory_to_blob(
        blob_service_client,
        container_name,
        CLEANED_DATA_DIR,
        blob_prefix="cleaned"
    )
    total_summary["uploaded"] += cleaned_summary["uploaded"]
    total_summary["failed"] += cleaned_summary["failed"]
    total_summary["skipped"] += cleaned_summary["skipped"]
    
    # Optionally upload gold data
    if upload_gold:
        logger.info(f"Uploading gold data from: {GOLD_DATA_DIR}")
        gold_summary = upload_directory_to_blob(
            blob_service_client,
            container_name,
            GOLD_DATA_DIR,
            blob_prefix="gold"
        )
        total_summary["uploaded"] += gold_summary["uploaded"]
        total_summary["failed"] += gold_summary["failed"]
        total_summary["skipped"] += gold_summary["skipped"]
    
    logger.info("=" * 60)
    logger.info("Azure Upload Summary:")
    logger.info(f"  Uploaded: {total_summary['uploaded']}")
    logger.info(f"  Failed:   {total_summary['failed']}")
    logger.info(f"  Skipped:  {total_summary['skipped']}")
    logger.info("=" * 60)
    
    return total_summary


if __name__ == "__main__":
    # Example usage: upload cleaned data using environment variables
    import sys
    
    # Check for environment variables
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    account_url_env = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
    
    credential = None
    if not conn_str and account_url_env:
        # Try to use service principal credentials
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        
        if all([tenant_id, client_id, client_secret]):
            credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    
    upload_gold = "--gold" in sys.argv
    
    summary = upload_cleaned_data(
        connection_string=conn_str,
        account_url=account_url_env,
        credential=credential,
        upload_gold=upload_gold
    )
    
    if "error" in summary:
        logger.error("Upload failed. Please check your Azure configuration.")
        sys.exit(1)
    else:
        logger.info("Upload completed successfully!")
        sys.exit(0)