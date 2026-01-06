# Skill Example 目录

此目录包含技能示例文件，用于演示如何组织和定义技能。

## 目录结构

每个技能应该包含以下文件：

```
skill_name/
├── skill.json          # 技能定义文件（必需）
├── content.md          # 技能详细内容（必需）
├── examples.json       # 使用示例（可选）
└── metadata.json       # 额外元数据（可选）
```

## 文件说明

### skill.json
技能的定义文件，包含：
- 技能基本信息（id, name, version, description）
- 分类和标签
- API 调用配置
- 依赖关系

### content.md
技能的详细内容，包含：
- 核心能力说明
- 工作流程
- API 调用说明
- 最佳实践

### examples.json
使用示例，包含：
- 不同场景的使用示例
- 输入/输出示例
- API 调用示例

### metadata.json
额外元数据，包含：
- 变更日志
- 相关技能
- 支持的语言
- 许可证信息

## 使用说明

运行 `init_database.py` 时，会自动从此目录加载技能并导入到数据库。

## 注意事项

- 不允许包含 `.py`、`.sh`、`.bash` 等脚本文件
- API URL 必须是 HTTPS
- 不允许 localhost 或内网 IP
- API 密钥存储在环境变量中，不在技能文件中

