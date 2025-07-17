from transformers import AutoTokenizer, AutoModelForCausalLM

# Название твоей модели
model_name = "devops-llm-10000"
repo_name = "PythonDevops/devops-llm-10000"  # заменим, если хочешь другое имя

# Загружаем токенизатор и модель из директории
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Пушим на Hugging Face
tokenizer.push_to_hub(repo_name)
model.push_to_hub(repo_name)