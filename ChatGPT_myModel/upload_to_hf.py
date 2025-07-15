from huggingface_hub import HfApi, HfFolder, Repository, snapshot_download, create_repo, upload_folder
from transformers import AutoModelForCausalLM, AutoTokenizer

# === Параметры ===
model_dir = "./final_model"
repo_name = "devops-llm"             # Название репозитория
hf_username = "Python"               # Твой username
hf_token = "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"  # Твой токен

# === Авторизация
HfFolder.save_token(hf_token)

# === Создание репозитория (если не существует)
api = HfApi()
full_repo_name = f"{hf_username}/{repo_name}"
try:
    api.create_repo(name=repo_name, token=hf_token, exist_ok=True, private=True)
    print(f"✅ Репозиторий {full_repo_name} готов.")
except Exception as e:
    print("⚠️ Ошибка при создании репозитория:", e)

# === Загрузка модели в Hugging Face Hub
upload_folder(
    repo_id=full_repo_name,
    folder_path=model_dir,
    path_in_repo=".",
    token=hf_token
)

print(f"\n🚀 Модель успешно загружена: https://huggingface.co/{full_repo_name}")