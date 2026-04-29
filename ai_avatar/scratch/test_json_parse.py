import json

def test_parsing(raw_content):
    print(f"Testing: {raw_content!r}")
    try:
        clean_content = raw_content.replace('```json', '').replace('```', '').strip()
        if "{" in clean_content and "}" in clean_content:
            start = clean_content.find("{")
            end = clean_content.rfind("}") + 1
            json_str = clean_content[start:end]
            data = json.loads(json_str)
        else:
            data = json.loads(clean_content)
        
        reply   = data.get("text", raw_content)
        emotion = data.get("emotion", "neutral")
        print(f"Parsed -> Reply: {reply!r}, Emotion: {emotion!r}")
    except Exception as e:
        print(f"Failed: {e}")

# Test cases
test_parsing('{"text": "Hello world", "emotion": "happy"}')
test_parsing('```json\n{"text": "Hello world", "emotion": "happy"}\n```')
test_parsing('Here is your answer: {"text": "Hello world", "emotion": "happy"} hope you like it')
test_parsing('Not a json at all')
