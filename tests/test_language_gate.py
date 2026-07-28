import yaml

from scripts.check_public_language import iter_yaml_prose, PORTUGUESE_PATTERN


def test_language_gate_allows_inline_multilingual_aliases():
    yaml_content = """
    team:
      name: Brazil
      aliases: ["Brazil", "Brasil", "BRA"]
    """
    parsed = yaml.safe_load(yaml_content)
    
    # Check that 'Brasil' doesn't get yielded by iter_yaml_prose
    extracted_strings = list(iter_yaml_prose(parsed))
    
    assert "Brazil" in extracted_strings
    assert "Brasil" not in extracted_strings
    assert "BRA" not in extracted_strings


def test_language_gate_allows_block_multilingual_aliases():
    yaml_content = """
    team:
      name: Brazil
      aliases:
        - Brazil
        - Brasil
        - BRA
    """
    parsed = yaml.safe_load(yaml_content)
    
    # Check that 'Brasil' doesn't get yielded by iter_yaml_prose
    extracted_strings = list(iter_yaml_prose(parsed))
    
    assert "Brazil" in extracted_strings
    assert "Brasil" not in extracted_strings
    assert "BRA" not in extracted_strings


def test_language_gate_still_rejects_portuguese_yaml_comments_or_other_fields():
    yaml_content = """
    team:
      name: Brazil
      description: "Este é um bolão de apostas."
    """
    parsed = yaml.safe_load(yaml_content)
    
    extracted_strings = list(iter_yaml_prose(parsed))
    assert "Este é um bolão de apostas." in extracted_strings
    
    # Ensure our pattern catches the Portuguese word "bolão"
    matches = [
        match.group(0) 
        for s in extracted_strings 
        for match in PORTUGUESE_PATTERN.finditer(s)
    ]
    assert "bolão" in [m.lower() for m in matches]
