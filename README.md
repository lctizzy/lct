# TK Video Analyzer

TikTok 视频分析工具 - 编导视角 · 菲律宾市场优化

## 功能
- TikTok URL 解析 + 视频下载
- Whisper 语音转写（支持他加禄语/英语）
- AI 四维分析（钩子/卖点/转化/适配度）
- 专为菲律宾咖啡/零食类目优化

## 部署到 Streamlit Cloud

1. 创建 GitHub 仓库，上传所有文件
2. 去 https://streamlit.io/cloud 注册
3. 点击 "New app" → 选择你的仓库
4. Branch: `main`，Main file path: `app.py`
5. 点击 "Deploy!"

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 配置

编辑 `config.py` 填入你的 MiniMax API Key：
```python
OPENAI_API_KEY = "你的Key"
```

或者在网页端直接输入 API Key。
