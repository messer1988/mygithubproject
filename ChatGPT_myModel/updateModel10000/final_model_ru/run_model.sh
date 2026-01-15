cat > run_model.sh <<'SH'
#!/usr/bin/env bash
set -e
source ~/devops-llm-env/bin/activate
cd /Users/mac/IdeaProjects/mygithubproject/ChatGPT_myModel/updateModel10000/final_model_ru
python3 gradio_chat_ru_pro.py
SH

chmod +x run_model.sh