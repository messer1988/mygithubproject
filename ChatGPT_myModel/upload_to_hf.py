from huggingface_hub import HfApi, HfFolder, upload_folder

# === Настройки ===
hf_token = "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"
hf_username = "Python"
repo_name = "devops-llm"
full_repo_id = f"{hf_username}/{repo_name}"
model_dir = "./final_model"

# === Авторизация
HfFolder.save_token(hf_token)
api = HfApi()

# === Создание репозитория (если ещё не существует)
if not any(repo.id == full_repo_id for repo in api.list_repos_objs(token=hf_token)):
    api.create_repo(repo_id=full_repo_id, private=True, token=hf_token)
    print(f"✅ Репозиторий {full_repo_id} создан.")
else:
    print(f"ℹ️ Репозиторий {full_repo_id} уже существует.")

# === Загрузка модели в репозиторий
upload_folder(
    repo_id=full_repo_id,
    folder_path=model_dir,
    path_in_repo=".",
    token=hf_token
)

print(f"\n🚀 Модель загружена: https://huggingface.co/{full_repo_id}")