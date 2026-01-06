"""
创建 Agent 模块
使用 LangChain 1.0 创建带有 Skills 功能的 Agent
"""

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from typing import Callable, Optional
import os
from dotenv import load_dotenv

from db_utils import DatabaseManager

# 加载环境变量
load_dotenv()


def create_load_skill_tool(db_manager: DatabaseManager, agent_name: str):
    """创建 load_skill 工具
    
    Args:
        db_manager: 数据库管理器
        agent_name: 角色名称
    
    Returns:
        load_skill 工具函数
    """
    @tool
    def load_skill(skill_name: str) -> str:
        """按需加载技能的完整内容到 agent 的上下文中。

        当你需要处理特定类型的请求时，使用此工具加载详细的技能信息。
        这将为你提供该技能领域的全面指导、策略和最佳实践。

        Args:
            skill_name: 要加载的技能名称
        
        Returns:
            技能的完整内容，包括指导原则、工作流程和最佳实践
        """
        # 从数据库获取技能
        skill = db_manager.get_skill(agent_name, skill_name)
        if skill:
            return f"已加载技能: {skill_name}\n\n{skill.content}"
        
        # 技能未找到，列出可用技能
        all_skills = db_manager.get_all_skills(agent_name)
        available = ", ".join(s["name"] for s in all_skills)
        return f"技能 '{skill_name}' 未找到。可用技能: {available}"
    
    return load_skill


class SkillMiddleware(AgentMiddleware):
    """将技能描述注入到系统提示中的中间件。
    
    这个中间件使技能可被发现，而无需预先加载其完整内容。
    它使用渐进式披露模式，让 agent 按需加载技能。
    """
    
    def __init__(self, db_manager: DatabaseManager, agent_name: str):
        """初始化并生成技能提示
        
        Args:
            db_manager: 数据库管理器
            agent_name: 角色名称
        """
        self.db_manager = db_manager
        self.agent_name = agent_name
        
        # 从数据库获取所有技能并构建技能提示
        skills = self.db_manager.get_all_skills(agent_name)
        skills_list = []
        for skill in skills:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)
        
        # 创建 load_skill 工具
        self.load_skill_tool = create_load_skill_tool(db_manager, agent_name)
    
    @property
    def tools(self):
        """返回工具列表（作为属性以支持动态加载）"""
        return [self.load_skill_tool]
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """同步：将技能描述注入到系统提示中"""
        # 构建技能附加内容
        skills_addendum = (
            f"\n\n## 可用技能\n\n{self.skills_prompt}\n\n"
            "当你需要处理特定类型的请求时，使用 load_skill 工具加载详细的技能信息。"
            "这将为你提供该技能领域的全面指导、策略和最佳实践。"
        )
        
        # 追加到系统消息的内容块
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)


def create_skills_agent(
    agent_name: str = "default_agent",
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    db_url: Optional[str] = None
):
    """创建带有技能功能的 agent
    
    Args:
        agent_name: 角色名称，默认为 "default_agent"
        model_name: 使用的模型名称，如果不提供则从环境变量 MODEL_NAME 读取，默认为 "gpt-4o"
        temperature: 模型温度参数，如果不提供则从环境变量 TEMPERATURE 读取，默认为 0.7
        api_key: OpenAI API 密钥，如果不提供则从环境变量 OPENAI_API_KEY 读取
        db_url: 数据库连接 URL，如果不提供则从环境变量 DATABASE_URL 读取
    
    Returns:
        配置好的 agent 实例
    """
    # 从环境变量读取配置（如果未提供参数）
    if model_name is None:
        model_name = os.getenv("MODEL_NAME", "gpt-4o")
    
    if temperature is None:
        temp_str = os.getenv("TEMPERATURE", "0.7")
        try:
            temperature = float(temp_str)
        except ValueError:
            temperature = 0.7
    
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    # 初始化数据库管理器
    db_manager = DatabaseManager(db_url)
    
    # 获取角色信息
    agent_info = db_manager.get_agent(agent_name)
    if not agent_info:
        raise ValueError(f"角色 '{agent_name}' 不存在。请先运行 init_database.py 初始化数据库。")
    
    # 获取系统提示词（如果角色有自定义提示词则使用，否则使用默认）
    system_prompt = agent_info.system_prompt or (
        "你是一个智能助手，拥有多种专业技能。"
        "你可以根据用户的需求，加载相应的技能来提供专业帮助。"
        "当你识别出需要特定专业知识的任务时，请先使用 load_skill 工具加载相关技能，"
        "然后基于该技能的指导来完成任务。"
    )
    
    # 初始化模型
    if api_key:
        llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
    else:
        llm = ChatOpenAI(model=model_name, temperature=temperature)
    
    # 创建检查点保存器（用于状态持久化）
    checkpointer = MemorySaver()
    
    # 创建技能中间件
    skill_middleware = SkillMiddleware(db_manager, agent_name)
    
    # 创建 agent，包含技能中间件
    agent = create_agent(
        model=llm,
        tools=[],  # 工具由中间件提供
        middleware=[skill_middleware],
        checkpointer=checkpointer,
        system_prompt=system_prompt,
    )
    
    return agent

