"""
数据库初始化脚本
创建数据库表并导入初始数据
"""

import os
from dotenv import load_dotenv
from db_utils import DatabaseManager, Agent, Skill
from load_skill_from_file import load_all_skills_from_example_dir

load_dotenv()


def init_database():
    """初始化数据库：创建表并导入初始数据"""
    
    # 检查数据库配置
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    if not db_user or not db_password or not db_name:
        print("错误: 未设置完整的数据库配置")
        print("请在 .env 文件中添加以下配置:")
        print("  DB_USER=postgres")
        print("  DB_PASSWORD=your-password")
        print("  DB_HOST=localhost (可选，默认 localhost)")
        print("  DB_PORT=5432 (可选，默认 5432)")
        print("  DB_NAME=skill (可选，默认 skill)")
        return
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    
    print(f"正在连接到数据库...")
    print(f"数据库: {db_name} @ {db_host}:{db_port}")
    print(f"用户: {db_user}")
    
    try:
        # 创建数据库管理器（自动从环境变量构建 URL）
        db = DatabaseManager()
        
        # 创建表
        print("\n正在创建数据库表...")
        db.create_tables()
        print("✓ 数据库表创建成功")
        
        # 创建默认角色
        print("\n正在创建默认角色...")
        default_agent_name = "default_agent"
        
        # 检查角色是否已存在
        existing_agent = db.get_agent(default_agent_name)
        if existing_agent:
            print(f"  角色 '{default_agent_name}' 已存在，跳过创建")
            agent = existing_agent
        else:
            agent = db.add_agent(
                name=default_agent_name,
                description="默认智能体角色，拥有多种专业技能",
                system_prompt=(
                    "你是一个智能助手，拥有多种专业技能。"
                    "你可以根据用户的需求，加载相应的技能来提供专业帮助。"
                    "当你识别出需要特定专业知识的任务时，请先使用 load_skill 工具加载相关技能，"
                    "然后基于该技能的指导来完成任务。"
                )
            )
            print(f"  ✓ 创建角色: {default_agent_name}")
        
        # 导入技能（从 skill-example 目录加载）
        print("\n正在导入技能到数据库...")
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        # 从 skill-example 目录加载技能
        example_skills = load_all_skills_from_example_dir("skill-example")
        
        if not example_skills:
            print("  警告: skill-example 目录中没有找到技能文件")
            print("  提示: 请在 skill-example 目录下创建技能文件夹，包含 skill.json 和 content.md 文件")
            print("  参考: skill-example/data_analysis/ 目录结构")
        else:
            print(f"  从 skill-example 目录找到 {len(example_skills)} 个技能")
            for skill_dir_name, (skill_json, content, examples, metadata) in example_skills.items():
                skill_id = skill_json.get("id", skill_dir_name)
                try:
                    # 检查技能是否已存在（按 skill_id 或 name）
                    existing_skill = db.get_skill(default_agent_name, skill_id)
                    if existing_skill:
                        print(f"  跳过: {skill_json.get('name')} (已存在)")
                        skipped_count += 1
                    else:
                        db.add_skill_from_json(
                            agent_name=default_agent_name,
                            skill_json=skill_json,
                            content=content,
                            examples=examples,
                            metadata=metadata,
                            content_file_path=f"skill-example/{skill_dir_name}/content.md"
                        )
                        print(f"  ✓ 导入: {skill_json.get('name')} (v{skill_json.get('version')})")
                        imported_count += 1
                except Exception as e:
                    print(f"  ✗ 导入失败 {skill_json.get('name')}: {str(e)}")
                    error_count += 1
        
        print(f"\n导入完成:")
        print(f"  - 成功导入: {imported_count} 个技能")
        print(f"  - 跳过: {skipped_count} 个技能（已存在）")
        if error_count > 0:
            print(f"  - 失败: {error_count} 个技能")
        print(f"\n✓ 数据库初始化完成！")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("数据库初始化工具")
    print("="*60)
    print()
    init_database()

