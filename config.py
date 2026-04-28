from pathlib import Path

# ========== TK视频分析器配置文件 ==========

# ---- GitHub 部署配置 ----
GITHUB_TOKEN = ""  # GitHub PAT（部署时在Streamlit环境变量中填写）
GITHUB_OWNER = "lctizzy"
GITHUB_REPO = "lct"

# ---- AI 分析配置 ----
# MiniMax API Key（在网页端输入，不要上传到GitHub）
OPENAI_API_KEY = ""
MODEL_NAME = "MiniMax-M2.7"
API_BASE = "https://api.minimaxi.com/v1"
FALLBACK_TO_LOCAL = True

# ---- 智谱 AI（GLM）配置 ----
ZHIPU_API_KEY = ""
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_MODEL = "glm-5.1"  # 可用：glm-5.1 / glm-5-turbo / glm-5 / glm-4.7 / glm-4.6 / glm-4.5

# ---- Whisper 语音识别配置 ----
WHISPER_MODEL = "small"  # tiny/base/small/medium — small比base准确率高7-10%
WHISPER_LANGUAGE = None  # None=自动检测

# ---- 视频处理配置 ----
MAX_VIDEO_SIZE_MB = 500
VIDEO_OUTPUT_DIR = "downloads"

# ---- 分析配置 ----
TARGET_MARKET = "菲律宾"
TARGET_LANGUAGE = "他加禄语"
TARGET_AUDIENCE_AGE = "18-35岁"
OUTPUT_LANGUAGE = "中文"

# ---- 分析报告配置 ----
REPORT_COMPACT_MODE = True
REPORT_MAX_TIPS = 3

REPORT_MODULES = [
    "文案提取",
    "钩子评估",
    "卖点分级",
    "转化结构",
    "适配评分",
    "优化建议",
]
