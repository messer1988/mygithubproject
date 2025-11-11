from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path

model_path = Path(__file__).resolve().parent
device = "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForCausalLM.from_pretrained(str(model_path)).to(device)
model.eval()

def ask(prompt):
    formatted = f"<|prompt|> {prompt}\n<|answer|>"
    inputs = tokenizer(formatted, return_tensors="pt").to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.8,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.convert_tokens_to_ids("<|prompt|>"),  # стоп при следующем вопросе
    )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # ✂️ оставляем только ответ
    if "<|answer|>" in text:
        text = text.split("<|answer|>")[-1]
    if "<|prompt|>" in text:
        text = text.split("<|prompt|>")[0]

    return text.strip()


while True:
    question = input("\n❓ Вопрос: ")
    if question.lower() in ["exit", "quit", "q"]:
        break
    print("\n🤖 Ответ:")
    print(ask(question))