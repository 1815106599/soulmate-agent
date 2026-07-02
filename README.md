# 🏆 社交匹配系统

多智能体对话式社交匹配系统，基于 **Agnes 2.0 Flash** 驱动。

通过自然聊天了解你的兴趣爱好、性格特点、社交偏好，然后从候选库中智能匹配志同道合的伙伴。

---

## 🚀 快速启动

### 方式一：双击运行（推荐）
双击项目根目录的 **`start_all.bat`**，自动启动后端 + 前端。

### 方式二：命令行
```powershell
cd 项目目录
.\start_all.bat
```

### 方式三：手动分别启动
```powershell
# 后端
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8001

# 前端（新开终端）
python -m streamlit run frontend/app.py --server.headless=true
```

---

## 📡 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 前端页面 | http://localhost:8501 | 聊天 + 匹配界面 |
| ⚙️ 后端API | http://localhost:8001 | REST API |
| 📖 API文档 | http://localhost:8001/docs | Swagger 接口文档 |

---

## 🧠 系统架构

```
用户输入 → Collector Agent (画像采集)
                ↓
        画像数据入库
                ↓
        Matcher Agent (匹配计算)
          ├─ 兴趣 Jaccard 相似度
          ├─ 性别匹配度
          ├─ 年龄相近度
          ├─ 性格兼容性
          ├─ 社交偏好匹配
          ├─ 目标匹配度
          └─ 向量语义相似度
                ↓
        Icebreaker Agent (破冰话术)
                ↓
         展示匹配结果
```

### 🧩 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **Collector** | `agents/collector.py` | 通过自然对话隐式采集用户画像 |
| **Matcher** | `agents/matcher.py` | 多维度加权评分，筛选排序候选人 |
| **Icebreaker** | `agents/icebreaker.py` | 根据共同点生成破冰话术 |
| **Backend** | `backend/app.py` | FastAPI 服务，会话管理 |
| **Frontend** | `frontend/app.py` | Streamlit 聊天 + 匹配界面 |
| **Config** | `backend/config.py` | 全局配置（API Key、向量维度等） |

### 📊 匹配维度与权重

| 维度 | 权重 | 说明 |
|------|------|------|
| 🎯 兴趣 | 0.30 | 支持近似匹配（"踢足球"↔"足球"） |
| 🧠 性格 | 0.15 | 相同性格加分，不同性格互补分 |
| 🤝 社交偏好 | 0.10 | 一对一/群体活动偏好匹配 |
| 🏆 目标 | 0.20 | 共同目标加分 |
| 📐 向量相似度 | 0.25 | 深度学习语义匹配 |
| 🎂 年龄加分 | +0.04 | 年龄越接近分越高 |
| 👤 性别加分 | +0.03 | 相同性别加分 |

---

## 💬 使用指南

1. 打开前端页面，像朋友聊天一样和AI对话
2. AI会通过聊天了解你的：昵称、年龄、兴趣、性格、社交偏好、匹配目标
3. 聊得差不多了，点击 **「🎯 开始匹配」**
4. 系统展示前5名最匹配的候选人，含详细信息和匹配度
5. 点击候选人可以查看详情，点 **「💬 生成破冰话术」** 获取聊天开场建议

---

## 🛠 开发说明

### 环境依赖

```
# 核心依赖
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
streamlit>=1.28.0
python-multipart>=0.0.6
aiosqlite>=0.19.0
```

### 项目结构

```
social-match-system/
├── agents/
│   ├── collector.py     # 画像采集Agent
│   ├── matcher.py       # 匹配决策Agent
│   └── icebreaker.py    # 破冰话术Agent
├── backend/
│   ├── app.py           # FastAPI 主服务
│   ├── config.py        # 配置文件
│   ├── models.py        # 数据模型
│   └── utils.py         # 工具函数（向量化等）
├── data/
│   └── demo_profiles.json  # 30个候选用户画像
├── frontend/
│   └── app.py           # Streamlit 前端界面
├── start_all.bat        # 一键启动（双击）
├── start_all.ps1        # 一键启动（脚本）
└── README.md            # 本文件
```

---

## 🛑 关闭服务

```powershell
# 停止后台运行服务
Stop-Job -Name SocialMatch-Backend, SocialMatch-Frontend

# 或手动结束 python 进程
taskkill /F /IM python.exe
```
