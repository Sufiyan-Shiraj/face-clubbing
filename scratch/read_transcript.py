import json

with open(r'C:\Users\DELL\.gemini\antigravity-ide\brain\58ec62c5-4892-45a5-9939-be331439d33f\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx in [602, 606, 610, 614]:
            print(f"=== Step {idx} ===")
            for tc in obj.get('tool_calls', []):
                print(tc.get('name'), tc.get('args', {}).get('TargetFile'))
                print('Prompt/Summary:', tc.get('args', {}).get('toolSummary'))
