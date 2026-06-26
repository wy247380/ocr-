# 专利证书可见内容核验系统 — 构建说明

## 项目结构

```
patent_verify_v2/
├── backend/                        # Python 后端
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 全局配置（数据目录 ~/.patent_verify/）
│   ├── models.py                   # SQLAlchemy ORM（8张表）
│   ├── database.py                 # 数据库引擎
│   ├── state_machine.py            # 状态机（18个状态）
│   ├── agent.py                    # 核心智能体编排
│   ├── routers/                    # API 路由
│   │   ├── upload.py               # 文件上传
│   │   ├── tasks.py                # 任务状态查询
│   │   ├── admin.py                # 人工审核
│   │   └── settings.py             # 系统设置（API Key、OCR引擎）
│   └── skills/                     # 11个 Skill 模块
│       ├── extract_visible_fields.py    # OCR 字段提取（EasyOCR + DeepSeek 纠错）
│       ├── deepseek_client.py           # DeepSeek API 客户端
│       ├── query_official.py            # 国知局查询（Playwright + CDP）
│       ├── compare_fields.py            # 字段比对
│       └── ...                          # 其余 skill
├── frontend/                       # Vue 3 前端
│   └── src/                        # 源代码
├── desktop/                        # 桌面打包
│   ├── desktop_app.py              # 桌面入口
│   ├── PatentVerifyAgent.spec      # PyInstaller 配置
│   ├── setup.iss                   # 完整安装脚本（Inno Setup）
│   ├── setup_upgrade.iss           # 升级补丁脚本
│   └── build_exe.bat               # 一键构建
└── README.md
```

## 核心架构

### OCR 流程（两大路径）
```
A. PDF 带文本层 → PyMuPDF 提取文字 → DeepSeek chat 解析（零 OCR 依赖）
B. 图片/扫描件 → EasyOCR（子进程隔离） → 正则提取 → DeepSeek chat 纠错
```

### 完整核验链路
```
上传 → classify → render(PyMuPDF) → preprocess → OCR(图片文本层双路径)
→ normalize → query(Playwright查国知局) → compare → decide(自动/人工)
```

### 关键技术决策
| 决策 | 选择 | 原因 |
|------|------|------|
| OCR 引擎 | EasyOCR | 中英文识别好，离线模型 ~115MB |
| PDF 渲染 | PyMuPDF(fitz) | 轻量、无依赖、300DPI |
| 官方查询 | Playwright + CDP | 绕过反爬，模拟真实浏览器 |
| 字段比对 | DeepSeek reasoner | 处理 OCR 误差、格式差异 |
| 状态管理 | 状态机（18态） | 严格转换规则，审计可追踪 |
| 数据存储 | SQLite | 单机部署，零配置 |

## 构建步骤

### 1. 开发环境
```bash
cd patent_verify_v2
pip install -r backend/requirements.txt
playwright install chromium
cd frontend && npm install
```

### 2. 启动开发模式
```bash
# 终端1：后端
cd backend && python -m uvicorn main:app --reload --port 8000
# 终端2：前端
cd frontend && npm run dev
```

### 3. 打包发布
```bash
# 步骤1：构建前端
cd frontend && npm run build

# 步骤2：PyInstaller 打包
cd .. && pyinstaller --clean desktop/PatentVerifyAgent.spec

# 步骤3：Inno Setup 安装包
ISCC.exe desktop/setup.iss

# 步骤3b：升级补丁（可选）
ISCC.exe desktop/setup_upgrade.iss
```

## 常见问题解决

### Win11 OCR 崩溃（cv2 冲突）
```
# 卸载冲突版本，锁定 headless 版
pip uninstall opencv-contrib-python -y
pip install opencv-python-headless==4.9.0.80 --force-reinstall
```

### Win11 程序文件写权限
程序安装到 `C:\Program Files\`，数据自动走 `C:\Users\<用户名>\.patent_verify\`

### 无 Chrome 浏览器
自动尝试：系统 Chrome → Playwright Chromium → 自动安装 Chromium
