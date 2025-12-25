from backend import pricing

def test_calculate_cost():
    # Test a known model
    # openai/gpt-5.2: 10.00 prompt, 30.00 completion (per 1M)
    # 100,000 prompt tokens = 0.1 * 10 = 1.0
    # 100,000 completion tokens = 0.1 * 30 = 3.0
    # Total = 4.0
    cost = pricing.calculate_cost("openai/gpt-5.2", 100000, 100000)
    assert cost == 4.0

def test_estimate_tokens():
    assert pricing.estimate_tokens("Hello world") == 2 # 11 // 4
    assert pricing.estimate_tokens("a" * 100) == 25

def test_format_cost():
    assert pricing.format_cost(0.001234) == "$0.0012"
    assert pricing.format_cost(0.1234) == "$0.123"
    assert pricing.format_cost(1.234) == "$1.23"
    assert pricing.format_cost(0) == "$0.00"

def test_calculate_total_stats():
    stage1 = [{"cost": 0.1, "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200}}]
    stage2 = [{"cost": 0.2, "usage": {"prompt_tokens": 200, "completion_tokens": 200, "total_tokens": 400}}]
    stage3 = {"cost": 0.3, "usage": {"prompt_tokens": 300, "completion_tokens": 300, "total_tokens": 600}}
    
    stats = pricing.calculate_total_stats(stage1, stage2, stage3)
    assert stats["total_cost"] == 0.6
    assert stats["total_tokens"]["total"] == 1200
    assert stats["total_tokens"]["prompt"] == 600
    assert stats["total_tokens"]["completion"] == 600
