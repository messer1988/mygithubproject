from huggingface_hub import HfApi, create_repo, upload_folder

repo_id = "PythonDevops/devops-llm-v2"  # новое имя, чтобы не перетирать старую
local_path = "./final_model"

api = HfApi()
create_repo(repo_id=repo_id, private=False, exist_ok=True)

upload_folder(
    repo_id=repo_id,
    folder_path=local_path,
    path_in_repo="."
)

print(f"✅ Uploaded {repo_id}")