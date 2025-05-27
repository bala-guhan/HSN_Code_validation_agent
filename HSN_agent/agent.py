import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from HSN_agent.__init__ import HSN_DICT
from typing import List, Dict, Union
from tqdm import tqdm

def validate_hsn_codes(codes: Union[str, List[str]]) -> Dict[str, dict]:
    """Validates multiple HSN codes for format requirements.

    Args:
        codes (Union[str, List[str]]): Single HSN code or list of HSN codes to validate.

    Returns:
        Dict[str, dict]: Dictionary with code as key and validation result as value.
    """
    # Convert single code to list for uniform processing
    if isinstance(codes, str):
        codes = [codes]
    
    results = {}
    for code in tqdm(codes, desc="Validating HSN codes"):
        # Check if code is between 2-8 digits
        if code.isdigit() and 2 <= len(code) <= 8 and len(code) % 2 == 0:
            results[code] = {
                "status": "success",
                "is_valid": True,
                "message": "HSN code format is valid."
            }
        else:
            results[code] = {
                "status": "error",
                "error_message": "HSN code format is invalid."
            }
    
    return results

def check_hierarchies(codes: Union[str, List[str]]) -> Dict[str, dict]:
    """Checks multiple HSN codes for valid hierarchy.

    Args:
        codes (Union[str, List[str]]): Single HSN code or list of HSN codes to check.

    Returns:
        Dict[str, dict]: Dictionary with code as key and hierarchy check result as value.
    """
    # Convert single code to list for uniform processing
    if isinstance(codes, str):
        codes = [codes]
    
    results = {}
    for code in tqdm(codes, desc="Checking hierarchies"):
        try:
            # Convert code to string if it's not already
            code = str(code)
            
            # Check if code exists in HSN dictionary
            if code not in HSN_DICT:
                results[code] = {
                    "status": "error",
                    "message": f"Code {code} not found in hierarchy"
                }
                continue
            
            # Check parent codes
            missing_parents = []
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent not in HSN_DICT:
                    missing_parents.append(parent)
            
            if missing_parents:
                results[code] = {
                    "status": "error",
                    "message": f"Parent codes {', '.join(missing_parents)} not found in hierarchy"
                }
            else:
                results[code] = {
                    "status": "success",
                    "message": "Valid hierarchy",
                    "description": HSN_DICT[code]
                }
                
        except Exception as e:
            results[code] = {
                "status": "error",
                "message": f"Error checking hierarchy: {str(e)}"
            }
    
    return results

def analyze_validation_results(codes: Union[str, List[str]]) -> str:
    """Analyzes and explains validation results for multiple HSN codes.

    Args:
        codes (Union[str, List[str]]): Single HSN code or list of HSN codes to analyze.

    Returns:
        str: Detailed analysis of validation results for all codes.
    """
    # Convert single code to list for uniform processing
    if isinstance(codes, str):
        codes = [codes]
    
    # Get validation results
    format_results = validate_hsn_codes(codes)
    hierarchy_results = check_hierarchies(codes)
    
    # Generate analysis
    analysis = "HSN Code Validation Analysis\n" + "=" * 30 + "\n\n"
    
    for code in codes:
        analysis += f"Code: {code}\n" + "-" * 20 + "\n"
        
        # Format validation results
        format_result = format_results[code]
        analysis += "1. Format Validation:\n"
        analysis += f"   • Status: {format_result['status']}\n"
        if format_result['status'] == 'success':
            analysis += "   • The code meets the basic format requirements:\n"
            analysis += "     - Contains only digits\n"
            analysis += "     - Length is between 2-8 digits\n"
            analysis += "     - Length is even (2, 4, 6, or 8 digits)\n"
        else:
            analysis += f"   • Issue: {format_result['error_message']}\n"
        
        # Hierarchy validation results
        hierarchy_result = hierarchy_results[code]
        analysis += "\n2. Hierarchy Validation:\n"
        analysis += f"   • Status: {hierarchy_result['status']}\n"
        if hierarchy_result['status'] == 'success':
            analysis += "   • The code exists in the HSN hierarchy\n"
            # Add description prominently
            analysis += f"\n   • Description:\n     {hierarchy_result['description']}\n"
            # Add parent code information with their descriptions
            analysis += "\n   • Parent Codes:\n"
            for i in range(2, len(code), 2):
                parent = code[:i]
                if parent in HSN_DICT:
                    analysis += f"     - {parent}: {HSN_DICT[parent]}\n"
        else:
            analysis += f"   • Issue: {hierarchy_result['message']}\n"
        
        # Overall assessment
        analysis += "\n3. Overall Assessment:\n"
        if format_result['status'] == 'success' and hierarchy_result['status'] == 'success':
            analysis += "   • The HSN code is completely valid\n"
            analysis += "   • It meets all format requirements\n"
            analysis += "   • It exists in the proper hierarchy\n"
            # Add final description summary
            analysis += f"\n   • Final Description:\n     {hierarchy_result['description']}\n"
        else:
            analysis += "   • The HSN code requires attention\n"
            if format_result['status'] == 'error':
                analysis += "   • Please correct the format issues first\n"
            if hierarchy_result['status'] == 'error':
                analysis += "   • Please verify the code exists in the HSN hierarchy\n"
        
        analysis += "\n" + "=" * 30 + "\n\n"
    
    print(analysis)
    return analysis

root_agent = Agent(
    name="hsn_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to validate and analyze multiple HSN codes with detailed format and hierarchy checks."
    ),
    instruction=(
        "You are a helpful agent who validates multiple HSN codes and provides detailed analysis. "
        "For each validation request:\n"
        "1. Process single or multiple HSN codes\n"
        "2. Validate each code's format (2-8 digits, even length)\n"
        "3. Check each code's existence in the HSN hierarchy\n"
        "4. Verify all parent codes exist for each code\n"
        "5. Provide comprehensive analysis of validation results\n"
        "6. Include descriptions of valid codes and their parent codes\n"
        "7. Give clear guidance on how to fix any issues found"
    ),
    tools=[validate_hsn_codes, check_hierarchies, analyze_validation_results],
)