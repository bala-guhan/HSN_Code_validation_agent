import pandas as pd
import logging
from typing import Dict, Set
from collections import defaultdict
from tqdm import tqdm
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables to store processed data
HSN_DICT: Dict[str, str] = {}
PARENT_CODES: Dict[str, Set[str]] = defaultdict(set)

def load_and_preprocess_data() -> None:
    """
    Load and preprocess HSN data from CSV file.
    This function is called once when the package is imported.
    """
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "data.csv")
        
        logger.info(f"Loading HSN data from {data_file}")
        
        # Load data
        df = pd.read_csv(data_file)
        
        # Convert HSN codes to strings and create dictionary
        df['HSNCode'] = df['HSNCode'].astype(str)
        global HSN_DICT
        HSN_DICT = dict(zip(df['HSNCode'], df['Description']))
        
        # Precompute parent codes
        logger.info("Precomputing parent codes...")
        for code in tqdm(HSN_DICT.keys(), desc="Processing HSN codes"):
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent in HSN_DICT:
                    PARENT_CODES[code].add(parent)
        
        logger.info(f"Successfully loaded {len(HSN_DICT)} HSN codes")
        logger.info(f"Successfully computed parent codes for {len(PARENT_CODES)} codes")
        
    except FileNotFoundError:
        logger.error(f"Data file not found at {data_file}")
        raise
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

def get_hsn_dict() -> Dict[str, str]:
    """Get the HSN code dictionary"""
    return HSN_DICT

def get_parent_codes() -> Dict[str, Set[str]]:
    """Get the parent codes dictionary"""
    return PARENT_CODES

def get_description(code: str) -> str:
    """Get description for a given HSN code"""
    return HSN_DICT.get(code, "Description not found")

# Load data when package is imported
try:
    load_and_preprocess_data()
except Exception as e:
    logger.error(f"Failed to initialize HSN data: {str(e)}")
    raise 