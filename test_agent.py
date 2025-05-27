import pytest
import pandas as pd
import os
from agent101 import Agent
import tempfile

# Test data
TEST_DATA = {
    'HSNCode': ['01', '0101', '010110', '010210', '01021010', '02', '0201', '020110'],
    'Description': [
        'Live animals',
        'Live horses, asses, mules and hinnies',
        'Pure-bred breeding animals',
        'Other live horses',
        'Detailed horse classification',
        'Meat and edible meat offal',
        'Meat of bovine animals, fresh or chilled',
        'Carcasses and half-carcasses'
    ]
}

INVALID_HSN_CODES = {
    'HSNCode': ['1', '123', '12345', '1234567', 'ABC', '12AB', '1234AB'],
    'Description': ['Invalid codes for testing'] * 7
}

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with test data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(TEST_DATA)
        df.to_csv(f.name, index=False)
        return f.name

@pytest.fixture
def agent():
    """Create an agent instance with test data"""
    agent = Agent()
    agent.data = pd.DataFrame(TEST_DATA)
    agent._preprocess_data()
    return agent

def test_agent_initialization():
    """Test agent initialization"""
    agent = Agent()
    assert agent.data is None
    assert agent.hsn_dict == {}
    assert agent.parent_codes == {}
    assert agent.conversation_history == []

def test_load_data(agent):
    """Test data loading and preprocessing"""
    assert agent.data is not None
    assert len(agent.hsn_dict) == len(TEST_DATA['HSNCode'])
    assert len(agent.parent_codes) == len(TEST_DATA['HSNCode'])

def test_single_valid_code_validation(agent):
    """Test validation of a single valid HSN code"""
    result = agent.validate_agent("010110")
    is_valid, conversation, (code, description) = result
    
    assert is_valid
    assert code == "010110"
    assert description == "Pure-bred breeding animals"
    assert any("Valid number" in msg for msg in conversation)
    assert any("Valid length" in msg for msg in conversation)
    assert any("Valid hierarchy" in msg for msg in conversation)

def test_single_invalid_code_validation(agent):
    """Test validation of a single invalid HSN code"""
    result = agent.validate_agent("12345")
    is_valid, conversation, (code, description) = result
    
    assert not is_valid
    assert code == "12345"
    assert description == "Description not found"
    assert any("Invalid length" in msg for msg in conversation)

def test_batch_validation(agent):
    """Test batch validation of multiple codes"""
    test_codes = ["010110", "12345", "02", "ABC"]
    results = agent.validate_agent(test_codes)
    
    assert len(results) == len(test_codes)
    assert results[0][0]  # First code should be valid
    assert not results[1][0]  # Second code should be invalid
    assert results[2][0]  # Third code should be valid
    assert not results[3][0]  # Fourth code should be invalid

def test_hierarchy_validation(agent):
    """Test hierarchical validation of codes"""
    # Test valid hierarchy
    result = agent.validate_agent("010110")
    assert result[0]  # Should be valid
    
    # Test invalid hierarchy (parent code doesn't exist)
    result = agent.validate_agent("999999")
    assert not result[0]  # Should be invalid

def test_number_validation(agent):
    """Test number validation"""
    # Test valid number
    result = agent.validate_agent("010110")
    assert result[0]  # Should be valid
    
    # Test invalid number
    result = agent.validate_agent("ABC123")
    assert not result[0]  # Should be invalid

def test_length_validation(agent):
    """Test length validation rules"""
    # Test valid lengths
    valid_codes = ["01", "0101", "010110", "01021010"]  # 2, 4, 6, 8 digits
    for code in valid_codes:
        result = agent.validate_agent(code)
        assert result[0], f"Code {code} should be valid"
        assert any("Valid length" in msg for msg in result[1])

    # Test invalid lengths
    invalid_codes = {
        "1": "too short (1 digit)",
        "123456789": "too long (9 digits)",
        "123": "odd length (3 digits)",
        "12345": "odd length (5 digits)"
    }
    
    for code, reason in invalid_codes.items():
        result = agent.validate_agent(code)
        assert not result[0], f"Code {code} should be invalid: {reason}"
        assert any("Invalid length" in msg for msg in result[1])

def test_cache_functionality(agent):
    """Test caching functionality"""
    # First validation
    result1 = agent.validate_agent("010110")
    cache_stats1 = agent.get_cache_stats()
    
    # Second validation of same code
    result2 = agent.validate_agent("010110")
    cache_stats2 = agent.get_cache_stats()
    
    assert result1 == result2  # Results should be identical
    assert cache_stats2['hits'] > cache_stats1['hits']  # Cache hit should increase

def test_memory_usage(agent):
    """Test memory usage tracking"""
    initial_memory = agent._get_memory_usage()
    
    # Perform some validations
    agent.validate_agent(["010110", "010210", "02"])
    
    final_memory = agent._get_memory_usage()
    assert final_memory >= initial_memory  # Memory usage should not decrease

def test_error_handling(agent):
    """Test error handling"""
    # Test invalid file format
    with pytest.raises(ValueError):
        agent.load_data("test.txt")
    
    # Test invalid input type
    with pytest.raises(TypeError):
        agent.validate_agent(123)  # Should be string or list

def test_conversation_history(agent):
    """Test conversation history tracking"""
    result = agent.validate_agent("010110")
    _, conversation, _ = result
    
    assert len(conversation) > 0
    assert any("number_validator" in msg for msg in conversation)
    assert any("length_validator" in msg for msg in conversation)
    assert any("hierarchical_validator" in msg for msg in conversation)
    assert any("final_result" in msg for msg in conversation)

def test_parent_codes_preprocessing(agent):
    """Test parent codes preprocessing"""
    code = "010110"
    assert code in agent.parent_codes
    assert "01" in agent.parent_codes[code]
    assert "0101" in agent.parent_codes[code]

def test_cleanup(temp_csv_file):
    """Test cleanup of temporary files"""
    # Ensure the temporary file is deleted
    os.unlink(temp_csv_file)
    assert not os.path.exists(temp_csv_file)

if __name__ == "__main__":
    pytest.main(["-v", "test_agent.py"]) 