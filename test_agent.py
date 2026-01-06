"""
Agent 测试用例
测试带有技能功能的 Agent
"""

import os
from dotenv import load_dotenv
from create_agent import create_skills_agent
from db_utils import DatabaseManager

load_dotenv()


def test_agent_creation():
    """测试 Agent 创建"""
    print("="*60)
    print("测试 1: Agent 创建")
    print("="*60)
    
    try:
        agent = create_skills_agent(agent_name="default_agent")
        print("✓ Agent 创建成功！")
        return agent
    except Exception as e:
        print(f"✗ Agent 创建失败: {str(e)}")
        return None


def test_skills_loading():
    """测试技能加载"""
    print("\n" + "="*60)
    print("测试 2: 技能加载")
    print("="*60)
    
    try:
        db = DatabaseManager()
        skills = db.get_all_skills("default_agent")
        
        print(f"✓ 成功加载 {len(skills)} 个技能:")
        for skill in skills:
            print(f"  - {skill['name']}: {skill['description']}")
        
        return True
    except Exception as e:
        print(f"✗ 技能加载失败: {str(e)}")
        return False


def test_agent_conversation(agent):
    """测试 Agent 对话"""
    print("\n" + "="*60)
    print("测试 3: Agent 对话")
    print("="*60)
    
    if agent is None:
        print("✗ Agent 未创建，跳过对话测试")
        return False
    
    try:
        # 创建对话配置
        thread_id = "test-thread"
        config = {"configurable": {"thread_id": thread_id}}
        
        # 测试查询
        test_queries = [
            "我需要分析一些数据，请告诉我应该怎么做？",
            "请帮我审查一段代码",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n测试查询 {i}: {query}")
            try:
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config=config
                )
                
                agent_response = response['messages'][-1].content
                print(f"✓ Agent 响应 (前200字符): {agent_response[:200]}...")
            except Exception as e:
                print(f"✗ 查询失败: {str(e)}")
        
        return True
    except Exception as e:
        print(f"✗ 对话测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("测试 0: 数据库连接")
    print("="*60)
    
    try:
        db = DatabaseManager()
        agents = db.get_all_agents()
        print(f"✓ 数据库连接成功")
        print(f"✓ 找到 {len(agents)} 个角色:")
        for agent in agents:
            skills_count = len(db.get_skills_by_agent(agent.name))
            print(f"  - {agent.name}: {skills_count} 个技能")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        print("\n提示: 请确保:")
        print("  1. PostgreSQL 服务正在运行")
        print("  2. .env 文件中的数据库配置正确（DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME）")
        print("  3. 已运行 init_database.py 初始化数据库")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Agent with Skills 测试套件")
    print("="*60)
    
    # 测试数据库连接
    if not test_database_connection():
        print("\n请先解决数据库连接问题，然后重新运行测试。")
        return
    
    # 测试技能加载
    if not test_skills_loading():
        print("\n请先运行 init_database.py 初始化数据库。")
        return
    
    # 测试 Agent 创建
    agent = test_agent_creation()
    
    # 测试 Agent 对话（需要 API 密钥）
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        test_agent_conversation(agent)
    else:
        print("\n跳过对话测试: 未设置 OPENAI_API_KEY")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()

