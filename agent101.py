import pandas as pd
from typing import Dict, List, Tuple, Union
from collections import defaultdict
import psutil
import time
from functools import lru_cache
import logging
from tqdm import tqdm

class Agent:
    def __init__(self, data=None):
        self.data = data
        self.conversation_history = []
        self.hsn_dict = {}
        self.parent_codes = defaultdict(set)
        self._initialize_agents()
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_agents(self):
        """Initialize all sub-agents with their validation functions"""
        self.agents = {
            'number_validator': self.number_validate,
            'length_validator': self.length_validate,
            'hierarchical_validator': self.hierarchical_validate
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB

    def load_data(self, filename: str) -> None:
        """Load and preprocess data from CSV or Excel file"""
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        self.logger.info(f"Loading data from {filename}")
        if filename.endswith('.csv'):
            self.data = pd.read_csv(filename)
        elif filename.endswith(('.xls', '.xlsx')):
            self.data = pd.read_excel(filename)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
        
        # Preprocess data
        self._preprocess_data()
        
        end_time = time.time()
        final_memory = self._get_memory_usage()
        self.logger.info(f"Data loaded and preprocessed in {end_time - start_time:.2f} seconds")
        self.logger.info(f"Memory usage: {final_memory - initial_memory:.2f} MB")

    def _preprocess_data(self) -> None:
        """Preprocess data for faster validation"""
        start_time = time.time()
        self.logger.info("Starting data preprocessing...")
        
        # Convert HSN codes to strings and create dictionary
        self.data['HSNCode'] = self.data['HSNCode'].astype(str)
        self.hsn_dict = dict(zip(self.data['HSNCode'], self.data['Description']))
        
        # Precompute parent codes for faster hierarchy validation
        self.logger.info("Precomputing parent codes...")
        self.parent_codes.clear()  # Clear existing parent codes
        
        # First, add all codes to parent_codes
        for code in self.hsn_dict.keys():
            self.parent_codes[code] = set()
            
        # Then, compute parent relationships
        for code in tqdm(self.hsn_dict.keys(), desc="Processing HSN codes"):
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent in self.hsn_dict:  # Only add if parent exists in our data
                    self.parent_codes[code].add(parent)
        
        end_time = time.time()
        self.logger.info(f"Preprocessing completed in {end_time - start_time:.2f} seconds")

    @lru_cache(maxsize=1000)
    def _validate_single_code(self, code: str) -> Tuple[bool, List[str], Tuple[str, str]]:
        """
        Internal method to validate a single HSN code with caching
        """
        # Reset conversation history
        self.conversation_history = []
        
        # Convert code to string if it's not already
        code = str(code)
        
        # Run all validations
        is_valid = True
        for agent_name, validator in self.agents.items():
            if agent_name == 'hierarchical_validator':
                valid, message = validator(code, self.hsn_dict)
            else:
                valid, message = validator(code)
            
            self.add_to_conversation(agent_name, message)
            is_valid = is_valid and valid

        # Add final validation result
        final_message = "Code is valid" if is_valid else "Code is invalid"
        self.add_to_conversation("final_result", final_message)

        # Get description if code exists in dictionary
        description = self.hsn_dict.get(code, "Description not found")
        code_info = (code, description)

        return is_valid, self.conversation_history, code_info

    def validate_agent(self, codes: Union[str, List[str]]) -> Union[Tuple[bool, List[str], Tuple[str, str]], List[Tuple[bool, List[str], Tuple[str, str]]]]:
        """
        Main validation method that runs all sub-agent validations
        Can handle both single code and list of codes
        """
        if self.data is None:
            raise ValueError("No data loaded. Please load data first using load_data()")

        start_time = time.time()
        
        # Handle single code input
        if isinstance(codes, str):
            result = self._validate_single_code(codes)
            end_time = time.time()
            self.logger.info(f"Single code validation completed in {end_time - start_time:.2f} seconds")
            return result
        
        # Handle list of codes
        elif isinstance(codes, list):
            results = []
            for code in tqdm(codes, desc="Validating codes"):
                result = self._validate_single_code(code)
                results.append(result)
            end_time = time.time()
            self.logger.info(f"Batch validation of {len(codes)} codes completed in {end_time - start_time:.2f} seconds")
            return results
        
        else:
            raise TypeError("Input must be either a string (single code) or list of strings (multiple codes)")

    def number_validate(self, code: str) -> Tuple[bool, str]:
        """Validate if the code contains only digits"""
        if code.isdigit():
            return True, "Valid number"
        else:
            return False, "Invalid number - contains non-digit characters"

    def length_validate(self, code: str) -> Tuple[bool, str]:
        """Validate if the code length is even and between 2 to 8 digits"""
        length = len(code)
        if length < 2:
            return False, "Invalid length - code must be at least 2 digits"
        elif length > 8:
            return False, "Invalid length - code must not exceed 8 digits"
        elif length % 2 != 0:
            return False, "Invalid length - code must have even number of digits"
        else:
            return True, "Valid length - even number of digits between 2 and 8"

    def hierarchical_validate(self, code: str, hsn_dict: Dict) -> Tuple[bool, str]:
        """Validate if all parent codes exist in the hierarchy using precomputed parent codes"""
        # First check if the code itself exists
        if code not in hsn_dict:
            return False, f"Code {code} not found in hierarchy"
            
        # Then check if all parent codes exist
        if code in self.parent_codes:
            missing_parents = []
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent not in hsn_dict:
                    missing_parents.append(parent)
            
            if missing_parents:
                return False, f"Parent codes {', '.join(missing_parents)} not found in hierarchy"
            return True, "Valid hierarchy - all parent codes exist"
        
        return False, "Invalid hierarchy - code not properly structured"

    def add_to_conversation(self, agent_name: str, message: str) -> None:
        """Add a message to the conversation history"""
        self.conversation_history.append(f"{agent_name}: {message}")

    def get_cache_stats(self) -> Dict:
        """Get statistics about the validation cache"""
        return {
            'cache_size': len(self._validate_single_code.cache_info()),
            'hits': self._validate_single_code.cache_info().hits,
            'misses': self._validate_single_code.cache_info().misses,
            'maxsize': self._validate_single_code.cache_info().maxsize
        }

# Example usage
if __name__ == "__main__":
    agent = Agent()
    agent.load_data("data.csv")

    # Single code validation
    print("\n=== Single Code Validation ===")
    input_code = input("Enter a HSN code: ")
    result = agent.validate_agent(input_code)
    is_valid, conversation, (code, description) = result
    print(f"\nValidation Results:")
    print(f"Code: {code}")
    print(f"Description: {description}")
    print(f"Is Valid: {is_valid}")
    print("\nAgent chat History>")
    for message in conversation:
        print(message)

    # Batch validation
    # print("\n=== Batch Validation ===")
    # test_codes = ["01", "0101", "010210", "999999"]
    # results = agent.validate_agent(test_codes)

    # for is_valid, conversation, (code, description) in results:
    #     print(f"\n=== Code: {code} ===")
    #     print(f"Description: {description}")
    #     print(f"Is Valid: {is_valid}")
    #     print("Agent chat History>")
    #     for message in conversation:
    #         print(message)

    # # Print cache statistics
    # print("\n=== Cache Statistics ===")
    # cache_stats = agent.get_cache_stats()
    # for key, value in cache_stats.items():
    #     print(f"{key}: {value}")

