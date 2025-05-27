from typing import AsyncGenerator, Dict, List, Tuple, Union, Optional
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
import pandas as pd
import psutil
import time
from functools import lru_cache
import logging
from tqdm import tqdm
from collections import defaultdict
from pydantic import Field

class HSNValidatorAgent(BaseAgent):
    """
    A BaseAgent implementation for HSN code validation.
    This agent validates HSN codes using multiple validation rules.
    """
    
    # Declare class fields for Pydantic
    data: Optional[pd.DataFrame] = Field(default=None, exclude=True)
    hsn_dict: Dict[str, str] = Field(default_factory=dict, exclude=True)
    parent_codes: Dict[str, set] = Field(default_factory=lambda: defaultdict(set), exclude=True)
    logger: Optional[logging.Logger] = Field(default=None, exclude=True)
    
    def __init__(self, name: str, data: pd.DataFrame = None):
        """
        Initialize the HSNValidatorAgent.
        
        Args:
            name: The name of the agent
            data: Optional DataFrame containing HSN codes and descriptions
        """
        # Initialize Pydantic model
        super().__init__(name=name)
        
        # Set instance attributes after Pydantic initialization
        self.data = data
        self._setup_logging()
        if data is not None:
            self._preprocess_data()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

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
        
        # Precompute parent codes
        self.logger.info("Precomputing parent codes...")
        self.parent_codes.clear()
        
        for code in self.hsn_dict.keys():
            self.parent_codes[code] = set()
            
        for code in tqdm(self.hsn_dict.keys(), desc="Processing HSN codes"):
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent in self.hsn_dict:
                    self.parent_codes[code].add(parent)
        
        end_time = time.time()
        self.logger.info(f"Preprocessing completed in {end_time - start_time:.2f} seconds")

    @lru_cache(maxsize=1000)
    def _validate_single_code(self, code: str) -> Tuple[bool, List[str], Tuple[str, str]]:
        """Internal method to validate a single HSN code with caching"""
        validation_results = []
        
        # Convert code to string if it's not already
        code = str(code)
        
        # Number validation
        is_valid_number = code.isdigit()
        validation_results.append(("number_validator", 
            "Valid number" if is_valid_number else "Invalid number - contains non-digit characters"))
        
        # Length validation
        length = len(code)
        is_valid_length = 2 <= length <= 8 and length % 2 == 0
        validation_results.append(("length_validator",
            "Valid length" if is_valid_length else "Invalid length - must be even and between 2-8 digits"))
        
        # Hierarchical validation
        is_valid_hierarchy = True
        hierarchy_message = "Valid hierarchy"
        if code not in self.hsn_dict:
            is_valid_hierarchy = False
            hierarchy_message = f"Code {code} not found in hierarchy"
        else:
            missing_parents = []
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent not in self.hsn_dict:
                    missing_parents.append(parent)
            if missing_parents:
                is_valid_hierarchy = False
                hierarchy_message = f"Parent codes {', '.join(missing_parents)} not found in hierarchy"
        
        validation_results.append(("hierarchical_validator", hierarchy_message))
        
        # Overall validation
        is_valid = is_valid_number and is_valid_length and is_valid_hierarchy
        validation_results.append(("final_result", "Code is valid" if is_valid else "Code is invalid"))
        
        # Get description
        description = self.hsn_dict.get(code, "Description not found")
        
        return is_valid, validation_results, (code, description)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Implement the validation logic for the agent.
        """
        self.logger.info(f"[{self.name}] Starting validation")
        
        # Get the input code from session state
        code = ctx.session.state.get("code")
        if not code:
            content = types.Content(
                role="assistant",
                parts=[types.Part(text="No code provided for validation")]
            )
            yield Event(author=self.name, content=content)
            return
        
        # Validate the code
        is_valid, validation_results, (code, description) = self._validate_single_code(code)
        
        # Create response content
        response_parts = [
            f"Code: {code}",
            f"Description: {description}",
            f"Is Valid: {is_valid}",
            "\nValidation Results:"
        ]
        
        for validator, message in validation_results:
            response_parts.append(f"{validator}: {message}")
        
        content = types.Content(
            role="assistant",
            parts=[types.Part(text="\n".join(response_parts))]
        )
        
        # Update session state
        ctx.session.state["validation_results"] = {
            "is_valid": is_valid,
            "code": code,
            "description": description,
            "validation_details": validation_results
        }
        
        yield Event(author=self.name, content=content)
        self.logger.info(f"[{self.name}] Validation completed")

# Example usage
if __name__ == "__main__":
    # Create an instance of the agent
    agent = HSNValidatorAgent(name="HSNValidator")
    
    # Load data (uncomment and provide your data file)
    agent.load_data("data.csv")
    
    # Create a simple session state
    session_state = {"code": "0101"}
    
    # Create a mock invocation context
    class MockInvocationContext:
        def __init__(self, state):
            self.session = type('Session', (), {'state': state})()
    
    # Run the agent
    async def run_agent():
        ctx = MockInvocationContext(session_state)
        async for event in agent._run_async_impl(ctx):
            print(f"\nEvent from {event.author}:")
            print(event.content.parts[0].text)
            print("\nSession state:")
            print(ctx.session.state)
    
    # Run the async function
    import asyncio
    asyncio.run(run_agent()) 