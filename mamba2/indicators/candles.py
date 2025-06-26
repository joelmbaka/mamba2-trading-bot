def is_green_candle(candle):
    """
    Check if a candle is green (bullish).
    A green candle has a closing price higher than its opening price.
    
    Args:
        candle: A dictionary or object with 'open' and 'close' attributes/keys
        
    Returns:
        bool: True if it's a green candle, False otherwise
    """
    return candle['close'] > candle['open']


def is_red_candle(candle):
    """
    Check if a candle is red (bearish).
    A red candle has a closing price lower than its opening price.
    
    Args:
        candle: A dictionary or object with 'open' and 'close' attributes/keys
        
    Returns:
        bool: True if it's a red candle, False otherwise
    """
    return candle['close'] < candle['open']

def is_doji(candle, doji_threshold=0.001):
    """
    Check if a candle is a doji (open and close nearly equal).
    
    Args:
        candle: Dictionary with 'open', 'high', 'low', 'close' keys
        doji_threshold: Maximum body-to-range ratio (default 0.1%)
        
    Returns:
        bool: True if body size is ≤ threshold of price range
    """
    price_range = abs(candle['high'] - candle['low'])
    if price_range == 0:
        return False
        
    body_size = abs(candle['close'] - candle['open'])
    return (body_size / price_range) <= doji_threshold

def is_shooting_star(candle, min_shadow_to_body_ratio=2.0):
    """
    Check if a candle is a shooting star pattern.
    A shooting star has a small real body near the low and a long upper shadow.
    
    Args:
        candle: A dictionary or object with 'open', 'high', 'low', 'close' attributes/keys
        min_shadow_to_body_ratio: Minimum ratio of upper shadow to body length (default 2.0)
        
    Returns:
        bool: True if it's a shooting star pattern, False otherwise
    """
    # Calculate body size and position
    body_size = abs(candle['close'] - candle['open'])
    upper_shadow = candle['high'] - max(candle['open'], candle['close'])
    
    # Calculate where the body is positioned
    body_position = (min(candle['open'], candle['close']) - candle['low'])
    
    # Shooting star conditions:
    # 1. Small body
    # 2. Long upper shadow (at least min_shadow_to_body_ratio times body size)
    # 3. Small or no lower shadow
    return (
        body_size > 0 and
        upper_shadow >= min_shadow_to_body_ratio * body_size and
        body_position <= body_size * 0.1  # Body near the low (10% tolerance)
    )


def is_hammer(candle, min_shadow_to_body_ratio=2.0):
    """
    Check if a candle is a hammer pattern.
    A hammer has a small real body near the high and a long lower shadow.
    
    Args:
        candle: A dictionary or object with 'open', 'high', 'low', 'close' attributes/keys
        min_shadow_to_body_ratio: Minimum ratio of lower shadow to body length (default 2.0)
        
    Returns:
        bool: True if it's a hammer pattern, False otherwise
    """
    # Calculate body size and position
    body_size = abs(candle['close'] - candle['open'])
    lower_shadow = min(candle['open'], candle['close']) - candle['low']
    
    # Calculate where the body is positioned
    body_position = candle['high'] - max(candle['open'], candle['close'])
    
    # Hammer conditions:
    # 1. Small body
    # 2. Long lower shadow (at least min_shadow_to_body_ratio times body size)
    # 3. Small or no upper shadow
    return (
        body_size > 0 and
        lower_shadow >= min_shadow_to_body_ratio * body_size and
        body_position <= body_size * 0.1  # Body near the high (10% tolerance)
    )