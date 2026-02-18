import random
from src.operators.op_syn_fake_tool_instruction_injection import apply

seed_text = "Summarize the following text in 3 bullet points."
SEED = 1234

for strength in [1,2,3,4,5]:
    rng = random.Random(SEED)
    ctx = {
        "strength": strength,
        "surface": "PROMPT_TEXT",
        "mode": "prepend",
        "constraints": {}
    }
    result = apply(seed_text, ctx, rng)
    print(f"\n=== strength={strength} ===")
    print(result.child_text)
