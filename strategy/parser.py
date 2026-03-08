import re

def parse_telegram_signal(text):
    if not text or not text.strip():
        return {"status": "empty"}

    lower_text = text.lower().strip()

    # 1. Mandatory Header Case-Insensitive with flexible spacing
    if not re.search(r'^trading\s*floor', lower_text):
        return {"status": "ignored", "reason": 'Does not start with "trading floor"'}

    # 2. Mandatory Sensex inclusion
    if 'sensex' not in lower_text:
        return {"status": "ignored", "reason": 'Does not contain "sensex"'}

    # 3. Strike Price Identification (Strict 5-digit)
    option_match = re.search(r'(\d{1,10})\s*(ce|pe)', lower_text)
    if not option_match:
        return {"status": "ignored", "reason": 'Strike/Type not found'}

    strike = option_match.group(1)
    if len(strike) != 5:
        return {"status": "ignored", "reason": f'Strike length is {len(strike)} (Need 5)'}

    option_type = option_match.group(2).upper()

    # 4. Entry Price Range (Strictly after "price" keyword)
    match_end_idx = option_match.end()
    remaining_text = lower_text[match_end_idx:]

    price_keyword_match = re.search(r'price', remaining_text)
    if not price_keyword_match:
        return {"status": "ignored", "reason": 'Keyword "price" not found after strike'}

    text_after_price = remaining_text[price_keyword_match.end():]
    price_match = re.search(r'@?\s*(\d{1,5})(?:\s*[-@]\s*(\d{1,5}))?', text_after_price)

    if not price_match:
        return {"status": "ignored", "reason": 'Price range not found after "price" keyword'}

    low = int(price_match.group(1))
    high = int(price_match.group(2)) if price_match.group(2) else low

    # 5. Average Logic
    average_match = re.search(r'(?:average|avg)\s*@?\s*(\d{1,5})', lower_text)
    if average_match:
        low = int(average_match.group(1))

    # 6. Validation Checks
    if high < low:
        return {"status": "ignored", "reason": 'High < Low'}
        
    diff = abs(high - low)
    if diff > 50:
        return {"status": "ignored", "reason": 'Range difference > 50'}

    return {
        "status": "valid",
        "index": "SENSEX",
        "strike": float(strike), # Keep as float/int for easy comparison with Kotak data
        "type": option_type,
        "low": low,
        "high": high,
        "diff": diff
    }