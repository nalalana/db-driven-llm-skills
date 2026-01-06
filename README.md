# LangChain 1.0 - Agent with Skills

这是一个使用 LangChain 1.0 框架实现的带有 Skills（技能）功能的智能 Agent 项目。技能和角色信息存储在 PostgreSQL 数据库中，支持动态管理和扩展。

## 功能特性

- ✅ **渐进式技能加载**：Agent 可以根据需要动态加载专业技能
- ✅ **角色管理**：支持多个智能体角色，每个角色拥有独立的技能集合
- ✅ **数据库存储**：使用 PostgreSQL 存储角色和技能，支持动态管理
- ✅ **模块化设计**：代码结构清晰，易于维护和扩展
- ✅ **中间件架构**：使用自定义中间件实现技能管理
- ✅ **状态持久化**：支持对话状态管理

## 项目结构

```
touming-llm-test/
├── requirements.txt          # 项目依赖
├── .env                      # 环境变量配置（需要创建）
├── skill-example/            # 技能示例目录
│   ├── data_analysis/        # 数据分析技能示例
│   │   ├── skill.json        # 技能定义文件（必需）
│   │   ├── content.md        # 技能详细内容（必需）
│   │   ├── examples.json     # 使用示例（可选）
│   │   └── metadata.json     # 元数据（可选）
│   ├── code_review/          # 代码审查技能示例
│   └── README.md             # 技能格式说明
├── db_utils.py               # 数据库工具类
├── load_skill_from_file.py   # 从文件加载技能的工具
├── init_database.py          # 数据库初始化脚本
├── create_agent.py           # Agent 创建模块
├── test_agent.py             # 测试用例
└── README.md                 # 项目文档
```

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 PostgreSQL 数据库

确保 PostgreSQL 服务正在运行，并创建数据库：

```sql
CREATE DATABASE skill;
```

### 3. 配置环境变量

创建 `.env` 文件并添加以下配置：

```env
# OpenAI API 配置（必需）
OPENAI_API_KEY=your-api-key-here

# 模型配置（可选，使用默认值）
MODEL_NAME=gpt-4o
TEMPERATURE=0.7

# PostgreSQL 数据库配置（必需）
DB_USER=postgres
DB_PASSWORD=your-password-here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skill
```

**配置说明：**
- `OPENAI_API_KEY`: OpenAI API 密钥（必需）
- `MODEL_NAME`: 使用的模型名称，默认为 `gpt-4o`
- `TEMPERATURE`: 模型温度参数（0-2），默认为 `0.7`
- `DB_USER`: PostgreSQL 数据库用户名（必需）
- `DB_PASSWORD`: PostgreSQL 数据库密码（必需）
- `DB_HOST`: PostgreSQL 数据库主机地址，默认为 `localhost`
- `DB_PORT`: PostgreSQL 数据库端口，默认为 `5432`
- `DB_NAME`: PostgreSQL 数据库名称，默认为 `skill`

### 4. 初始化数据库

运行初始化脚本创建数据库表并导入初始数据：

```bash
python init_database.py
```

这个脚本会：
- 创建所有数据库表（agents, skills, skill_api_calls, skill_requirements, skill_sync_log）
- 创建默认角色 `default_agent`
- 从 `skill-example` 目录加载所有技能文件
- 如果 `skill-example` 目录为空，会显示警告提示

## 使用方法

### 基本使用

```python
from create_agent import create_skills_agent

# 创建默认角色的 Agent
agent = create_skills_agent(agent_name="default_agent")

# 创建对话配置
thread_id = "my-conversation"
config = {"configurable": {"thread_id": thread_id}}

# 与 agent 对话
response = agent.invoke(
    {"messages": [{"role": "user", "content": "帮我分析一下数据"}]},
    config=config
)

print(response['messages'][-1].content)
```

### 运行测试

```bash
python test_agent.py
```

测试包括：
- 数据库连接测试
- 技能加载测试
- Agent 创建测试
- Agent 对话测试（需要 API 密钥）

## 数据库结构

### agents 表（智能体角色）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | VARCHAR(100) | 角色名称（唯一） |
| description | TEXT | 角色描述 |
| system_prompt | TEXT | 系统提示词 |
| enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### skills 表（技能主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| skill_id | VARCHAR(100) | 技能ID（唯一，对应skill.json中的id） |
| name | VARCHAR(200) | 技能名称 |
| short_description | TEXT | 简短描述 |
| description | TEXT | 详细描述 |
| version | VARCHAR(20) | 版本号 |
| category | VARCHAR(50) | 分类 |
| tags | ARRAY | 标签数组 |
| author | VARCHAR(100) | 作者 |
| content | TEXT | 技能详细内容（content.md） |
| content_file_path | VARCHAR(500) | Gitee repo中的文件路径 |
| examples | JSONB | 使用示例（examples.json） |
| metadata_json | JSONB | 额外元数据（metadata.json） |
| status | VARCHAR(20) | 状态：active, deprecated, archived |
| priority | INTEGER | 优先级 |
| agent_id | INTEGER | 所属角色ID（外键） |
| enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| last_synced_at | TIMESTAMP | 最后从Gitee同步的时间 |
| gitee_repo_url | VARCHAR(500) | Gitee repo URL |
| gitee_commit_hash | VARCHAR(100) | 对应的commit hash |

### skill_api_calls 表（API调用配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| skill_id | INTEGER | 技能ID（外键） |
| api_name | VARCHAR(100) | API名称 |
| method | VARCHAR(10) | HTTP方法：GET, POST, PUT, DELETE |
| url | TEXT | API URL |
| description | TEXT | API描述 |
| required_params | JSONB | 必需参数列表 |
| optional_params | JSONB | 可选参数列表 |
| auth_type | VARCHAR(20) | 认证类型：bearer, api_key, oauth2, none |
| auth_config | JSONB | 认证配置 |
| request_headers | JSONB | 请求头配置 |
| request_body_template | TEXT | 请求体模板 |
| response_format | JSONB | 响应格式说明 |
| timeout_seconds | INTEGER | 超时时间（秒） |
| retry_count | INTEGER | 重试次数 |
| enabled | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### skill_requirements 表（技能依赖关系）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| skill_id | INTEGER | 技能ID（外键） |
| requirement_type | VARCHAR(50) | 依赖类型：dependency, api_key, min_version |
| requirement_name | VARCHAR(200) | 依赖的技能ID或API密钥名称 |
| requirement_value | TEXT | 版本号或其他值 |
| is_required | BOOLEAN | 是否必需 |
| created_at | TIMESTAMP | 创建时间 |

### skill_sync_log 表（同步日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| skill_id | INTEGER | 技能ID（外键） |
| sync_type | VARCHAR(20) | 同步类型：full, incremental |
| gitee_commit_hash | VARCHAR(100) | Gitee commit hash |
| sync_status | VARCHAR(20) | 同步状态：success, failed, partial |
| sync_message | TEXT | 同步消息或错误信息 |
| files_updated | ARRAY | 更新的文件列表 |
| sync_duration_ms | INTEGER | 同步耗时（毫秒） |
| synced_at | TIMESTAMP | 同步时间 |

**关系**：
- 一个角色（agent）可以有多个技能（skill），通过 `agent_id` 关联
- 一个技能可以有多个 API 调用配置（skill_api_call），通过 `skill_id` 关联
- 一个技能可以有多个依赖关系（skill_requirement），通过 `skill_id` 关联

## 技能文件格式

### 推荐格式（skill-example 目录）

每个技能应该包含以下文件：

```
skill_name/
├── skill.json          # 技能定义文件（必需）
├── content.md          # 技能详细内容（必需）
├── examples.json       # 使用示例（可选）
└── metadata.json       # 额外元数据（可选）
```

#### skill.json 示例

```json
{
  "id": "data_analysis",
  "name": "数据分析",
  "version": "1.0.0",
  "description": "专业的数据分析技能",
  "short_description": "数据分析专家",
  "category": "analysis",
  "tags": ["data", "analysis"],
  "author": "team-name",
  "status": "active",
  "priority": 10,
  "content_file": "content.md",
  "examples_file": "examples.json",
  "requirements": {
    "min_agent_version": "1.0.0",
    "dependencies": [],
    "api_keys": []
  },
  "api_calls": [
    {
      "name": "get_data_statistics",
      "method": "POST",
      "url": "https://api.example.com/v1/statistics",
      "description": "获取数据统计信息",
      "required_params": ["data_id"],
      "optional_params": ["format"],
      "auth_type": "bearer",
      "auth_config": {
        "header_name": "Authorization",
        "token_env": "STAT_API_KEY"
      }
    }
  ],
  "metadata": {
    "estimated_tokens": 500,
    "execution_time": "1-5s",
    "complexity": "medium"
  }
}
```

详细格式说明请参考 `skill-example/README.md`

## 管理角色和技能

### 使用 Python 代码

#### 从文件加载技能（推荐）

```python
from db_utils import DatabaseManager
from load_skill_from_file import load_skill_from_directory

db = DatabaseManager()

# 从 skill-example 目录加载技能
skill_json, content, examples, metadata = load_skill_from_directory(
    "skill-example/data_analysis"
)

# 添加到数据库
skill = db.add_skill_from_json(
    agent_name="default_agent",
    skill_json=skill_json,
    content=content,
    examples=examples,
    metadata=metadata,
    content_file_path="skill-example/data_analysis/content.md"
)
```

#### 直接添加技能（便捷方法，仅用于测试）

```python
from db_utils import DatabaseManager

db = DatabaseManager()

# 创建新角色
agent = db.add_agent(
    name="data_scientist",
    description="数据科学家角色",
    system_prompt="你是一个专业的数据科学家..."
)

# 为角色添加技能（便捷方法，仅用于快速测试）
# 注意：生产环境请使用 add_skill_from_json 或从文件加载
skill = db.add_skill(
    agent_name="data_scientist",
    name="machine_learning",
    description="机器学习技能",
    content="详细的机器学习指导内容..."
)

# 获取角色的所有技能
skills = db.get_skills_by_agent("data_scientist")

# 获取特定技能（支持按 name 或 skill_id 查询）
skill = db.get_skill("data_scientist", "machine_learning")
```

### 使用 SQL

```sql
-- 创建新角色
INSERT INTO agents (name, description, system_prompt, enabled)
VALUES ('data_scientist', '数据科学家角色', '系统提示词...', true);

-- 为角色添加技能（新格式）
INSERT INTO skills (
    skill_id, name, short_description, description, version,
    category, tags, content, agent_id, enabled, status, priority
)
VALUES (
    'machine_learning',
    '机器学习',
    '机器学习专家',
    '详细的机器学习技能描述...',
    '1.0.0',
    'development',
    ARRAY['ml', 'ai', 'python'],
    '详细的机器学习指导内容...',
    (SELECT id FROM agents WHERE name = 'data_scientist'),
    true,
    'active',
    10
);

-- 添加 API 调用配置
INSERT INTO skill_api_calls (
    skill_id, api_name, method, url, description,
    required_params, auth_type, enabled
)
VALUES (
    (SELECT id FROM skills WHERE skill_id = 'machine_learning'),
    'train_model',
    'POST',
    'https://api.example.com/v1/train',
    '训练机器学习模型',
    '["model_type", "data"]'::jsonb,
    'bearer',
    true
);

-- 查询角色的所有技能
SELECT s.* FROM skills s
JOIN agents a ON s.agent_id = a.id
WHERE a.name = 'data_scientist' AND s.enabled = true
ORDER BY s.priority DESC, s.name;

-- 查询技能的 API 调用配置
SELECT * FROM skill_api_calls
WHERE skill_id = (SELECT id FROM skills WHERE skill_id = 'machine_learning')
AND enabled = true;

-- 禁用技能
UPDATE skills SET enabled = false WHERE skill_id = 'machine_learning';
```

## 预定义技能

项目在 `skill-example` 目录中包含以下预定义技能：

1. **data_analysis** - 数据分析专家
   - 数据清洗、统计分析、可视化、报告生成
   - 包含 API 调用配置示例

2. **code_review** - 代码审查专家
   - 代码质量检查、性能优化、安全审查、最佳实践

**注意**：所有技能必须按照标准格式存放在 `skill-example` 目录下。初始化脚本会从该目录加载所有技能文件。

## 工作原理

### 技能加载机制

1. **技能发现**：`SkillMiddleware` 从数据库加载角色的所有技能，将技能描述注入到系统提示中
2. **按需加载**：当 Agent 识别出需要特定技能时，会调用 `load_skill` 工具
3. **上下文增强**：加载的技能内容会被添加到对话上下文中，指导 Agent 的行为

### 架构设计

```
用户查询
    ↓
Agent (create_agent)
    ↓
SkillMiddleware (从数据库加载技能描述)
    ↓
LLM 决策
    ↓
load_skill 工具 (从数据库按需加载技能)
    ↓
增强的上下文
    ↓
专业化的响应
```

### 数据流

```
skill-example/ 目录（技能文件）
    ├── skill.json
    ├── content.md
    ├── examples.json
    └── metadata.json
         ↓
load_skill_from_file.py（加载技能文件）
         ↓
init_database.py（导入到数据库）
         ↓
PostgreSQL 数据库
    ├── agents 表（角色信息）
    ├── skills 表（技能信息，关联到角色）
    ├── skill_api_calls 表（API调用配置）
    ├── skill_requirements 表（依赖关系）
    └── skill_sync_log 表（同步日志）
         ↓
DatabaseManager（数据库工具类）
         ↓
create_agent（创建 Agent）
         ↓
SkillMiddleware（技能中间件）
         ↓
Agent（智能体）
```

## 代码文件说明

### 1. db_utils.py
数据库工具类，提供：
- `DatabaseManager`：数据库管理器
- `Agent`、`Skill`、`SkillApiCall`、`SkillRequirement`、`SkillSyncLog`：数据模型
- 角色和技能的 CRUD 操作
- `add_skill_from_json()`：从 JSON 格式添加技能（支持新格式）
- `get_skill_api_calls()`：获取技能的 API 调用配置
- `add_sync_log()`：添加同步日志

### 2. load_skill_from_file.py
从文件加载技能的工具：
- `load_skill_from_directory()`：从技能目录加载所有文件
- `load_all_skills_from_example_dir()`：从 skill-example 目录加载所有技能

### 3. init_database.py
数据库初始化脚本：
- 创建所有数据库表（agents, skills, skill_api_calls, skill_requirements, skill_sync_log）
- 创建默认角色
- 从 `skill-example` 目录加载所有技能文件（标准格式）

### 4. create_agent.py
Agent 创建模块：
- `create_skills_agent()`：创建带有技能功能的 Agent
- `SkillMiddleware`：技能中间件
- `create_load_skill_tool()`：创建技能加载工具

### 5. test_agent.py
测试用例：
- 数据库连接测试
- 技能加载测试
- Agent 创建和对话测试

## 技术栈

- **LangChain 1.0**：核心框架
- **LangGraph**：Agent 运行时
- **OpenAI GPT-4**：语言模型（可替换为其他模型）
- **PostgreSQL**：关系型数据库
- **SQLAlchemy**：Python ORM
- **Python 3.8+**：编程语言

## 常见问题

### 1. 数据库连接失败

**问题**：`psycopg2.OperationalError: could not connect to server`

**解决方案**：
- 确保 PostgreSQL 服务正在运行
- 检查 `.env` 文件中的数据库配置是否正确（`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`）
- 确认数据库已创建
- 检查用户名和密码是否正确

### 2. 表不存在

**问题**：`relation "agents" does not exist`

**解决方案**：运行初始化脚本
```bash
python init_database.py
```

### 3. 角色不存在

**问题**：`ValueError: 角色 'xxx' 不存在`

**解决方案**：
- 确保已运行 `init_database.py` 创建默认角色
- 或使用 `DatabaseManager.add_agent()` 创建新角色

### 4. API 密钥错误

**问题**：`AuthenticationError: Invalid API key`

**解决方案**：检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确

## 技能管理最佳实践

### 添加新技能

1. **在 skill-example 目录创建技能文件夹**
   ```
   skill-example/your_skill_name/
   ├── skill.json
   ├── content.md
   ├── examples.json (可选)
   └── metadata.json (可选)
   ```

2. **运行初始化脚本**
   ```bash
   python init_database.py
   ```
   脚本会自动检测并导入新技能

3. **验证技能**
   ```bash
   python test_agent.py
   ```

### 技能文件规范

- **skill.json**：必须包含 id, name, version, description 等字段
- **content.md**：使用 Markdown 格式，包含技能详细说明
- **API 调用**：URL 必须是 HTTPS，不允许 localhost 或内网 IP
- **安全限制**：不允许包含 .py、.sh 等脚本文件

### Gitee 托管

技能文件可以托管在 Gitee 仓库中：
- 支持通过 Webhook 自动同步
- 记录 commit hash 用于版本追踪
- 支持增量同步更新

## 扩展建议

1. **多角色支持**：为不同场景创建不同的角色和技能组合
2. **技能版本管理**：使用 version 字段跟踪技能变更，支持回滚
3. **技能分类**：使用 category 和 tags 字段对技能进行分组和搜索
4. **使用统计**：记录技能使用情况，优化技能推荐
5. **权限管理**：为不同用户分配不同的角色和技能
6. **缓存优化**：对频繁访问的技能添加缓存层
7. **API 调用管理**：统一管理技能中的 API 调用配置和认证
8. **同步机制**：实现从 Gitee 自动同步技能更新

## 注意事项

- 确保 PostgreSQL 服务正在运行
- 定期备份数据库
- 技能内容会占用 token，注意控制技能内容的长度
- 建议在生产环境中使用连接池
- 保护数据库密码，不要提交到版本控制系统

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
