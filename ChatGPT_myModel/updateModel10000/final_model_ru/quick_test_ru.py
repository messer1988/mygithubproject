from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path

# ⚙️ Путь к модели — текущая папка, без /final_model_ru
model_path = Path(__file__).resolve().parent

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🚀 Loading model from: {model_path}")
print(f"Using device: {device}")

tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForCausalLM.from_pretrained(str(model_path)).to(device)
model.eval()

prompt = "Как работает Ansible?"
inputs = tokenizer(f"<|prompt|> {prompt}\n<|answer|>", return_tensors="pt").to(device)
outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.8, top_p=0.95, do_sample=True)
print("\n🤖 Ответ:\n", tokenizer.decode(outputs[0], skip_special_tokens=True))