"""
数据库工具类
用于连接和操作 PostgreSQL 数据库
"""

from sqlalchemy import create_engine, Column, String, Text, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Agent(Base):
    """智能体角色表"""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='角色名称')
    description = Column(Text, comment='角色描述')
    system_prompt = Column(Text, comment='系统提示词')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关联关系：一个角色可以有多个技能
    skills = relationship("Skill", back_populates="agent", cascade="all, delete-orphan")


class Skill(Base):
    """技能表"""
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(100), unique=True, nullable=False, comment='技能ID（对应skill.json中的id）')
    name = Column(String(200), nullable=False, comment='技能名称')
    short_description = Column(Text, comment='简短描述')
    description = Column(Text, nullable=False, comment='详细描述')
    version = Column(String(20), nullable=False, comment='版本号')
    category = Column(String(50), comment='分类')
    tags = Column(ARRAY(String), comment='标签数组')
    author = Column(String(100), comment='作者')
    content = Column(Text, nullable=False, comment='技能详细内容（content.md）')
    content_file_path = Column(String(500), comment='Gitee repo中的文件路径')
    examples = Column(JSONB, comment='使用示例（examples.json）')
    metadata_json = Column(JSONB, comment='额外元数据（metadata.json）')
    status = Column(String(20), default='active', comment='状态：active, deprecated, archived')
    priority = Column(Integer, default=0, comment='优先级')
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False, comment='所属角色ID')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    last_synced_at = Column(DateTime(timezone=True), comment='最后从Gitee同步的时间')
    gitee_repo_url = Column(String(500), comment='Gitee repo URL')
    gitee_commit_hash = Column(String(100), comment='对应的commit hash')
    
    # 关联关系
    agent = relationship("Agent", back_populates="skills")
    api_calls = relationship("SkillApiCall", back_populates="skill", cascade="all, delete-orphan")
    requirements = relationship("SkillRequirement", back_populates="skill", cascade="all, delete-orphan")


class SkillApiCall(Base):
    """技能API调用配置表"""
    __tablename__ = 'skill_api_calls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False, comment='技能ID')
    api_name = Column(String(100), nullable=False, comment='API名称')
    method = Column(String(10), nullable=False, comment='HTTP方法：GET, POST, PUT, DELETE')
    url = Column(Text, nullable=False, comment='API URL')
    description = Column(Text, comment='API描述')
    required_params = Column(JSONB, comment='必需参数列表')
    optional_params = Column(JSONB, comment='可选参数列表')
    auth_type = Column(String(20), comment='认证类型：bearer, api_key, oauth2, none')
    auth_config = Column(JSONB, comment='认证配置')
    request_headers = Column(JSONB, comment='请求头配置')
    request_body_template = Column(Text, comment='请求体模板')
    response_format = Column(JSONB, comment='响应格式说明')
    timeout_seconds = Column(Integer, default=30, comment='超时时间（秒）')
    retry_count = Column(Integer, default=0, comment='重试次数')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关联关系
    skill = relationship("Skill", back_populates="api_calls")


class SkillRequirement(Base):
    """技能依赖关系表"""
    __tablename__ = 'skill_requirements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False, comment='技能ID')
    requirement_type = Column(String(50), nullable=False, comment='依赖类型：dependency, api_key, min_version')
    requirement_name = Column(String(200), nullable=False, comment='依赖的技能ID或API密钥名称')
    requirement_value = Column(Text, comment='版本号或其他值')
    is_required = Column(Boolean, default=True, comment='是否必需')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    
    # 关联关系
    skill = relationship("Skill", back_populates="requirements")


class SkillSyncLog(Base):
    """技能同步日志表"""
    __tablename__ = 'skill_sync_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False, comment='技能ID')
    sync_type = Column(String(20), nullable=False, comment='同步类型：full, incremental')
    gitee_commit_hash = Column(String(100), comment='Gitee commit hash')
    sync_status = Column(String(20), nullable=False, comment='同步状态：success, failed, partial')
    sync_message = Column(Text, comment='同步消息或错误信息')
    files_updated = Column(ARRAY(String), comment='更新的文件列表')
    sync_duration_ms = Column(Integer, comment='同步耗时（毫秒）')
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), comment='同步时间')


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_url: Optional[str] = None):
        """初始化数据库连接
        
        Args:
            db_url: 数据库连接 URL，如果不提供则从环境变量构建
        """
        if db_url:
            self.db_url = db_url
        else:
            # 从环境变量读取数据库配置
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "skill")
            
            # 构建数据库连接 URL
            self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # 创建数据库引擎
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """创建数据库表（如果不存在）"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    # ========== Agent 相关方法 ==========
    
    def add_agent(self, name: str, description: str = "", system_prompt: str = "") -> Agent:
        """添加新角色
        
        Args:
            name: 角色名称
            description: 角色描述
            system_prompt: 系统提示词
            
        Returns:
            创建的 Agent 对象
        """
        session = self.get_session()
        try:
            agent = Agent(
                name=name,
                description=description,
                system_prompt=system_prompt,
                enabled=True
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """获取角色
        
        Args:
            agent_name: 角色名称
            
        Returns:
            Agent 对象，如果不存在则返回 None
        """
        session = self.get_session()
        try:
            return session.query(Agent).filter(
                Agent.name == agent_name,
                Agent.enabled == True
            ).first()
        finally:
            session.close()
    
    def get_all_agents(self) -> List[Agent]:
        """获取所有启用的角色"""
        session = self.get_session()
        try:
            return session.query(Agent).filter(Agent.enabled == True).all()
        finally:
            session.close()
    
    # ========== Skill 相关方法 ==========
    
    def add_skill_from_json(
        self,
        agent_name: str,
        skill_json: Dict,
        content: str,
        examples: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        content_file_path: Optional[str] = None,
        gitee_repo_url: Optional[str] = None,
        gitee_commit_hash: Optional[str] = None
    ) -> Skill:
        """从 JSON 定义添加技能到指定角色
        
        Args:
            agent_name: 角色名称
            skill_json: skill.json 的内容
            content: content.md 的内容
            examples: examples.json 的内容（可选）
            metadata: metadata.json 的内容（可选）
            content_file_path: Gitee repo 中的文件路径（可选）
            gitee_repo_url: Gitee repo URL（可选）
            gitee_commit_hash: Gitee commit hash（可选）
            
        Returns:
            创建的 Skill 对象
        """
        session = self.get_session()
        try:
            # 在同一个 session 中查询 agent
            agent = session.query(Agent).filter(
                Agent.name == agent_name,
                Agent.enabled == True
            ).first()
            
            if not agent:
                raise ValueError(f"角色 '{agent_name}' 不存在")
            
            # 创建技能
            skill = Skill(
                skill_id=skill_json.get("id"),
                name=skill_json.get("name"),
                short_description=skill_json.get("short_description"),
                description=skill_json.get("description"),
                version=skill_json.get("version", "1.0.0"),
                category=skill_json.get("category"),
                tags=skill_json.get("tags", []),
                author=skill_json.get("author"),
                content=content,
                content_file_path=content_file_path,
                examples=examples,
                metadata_json=metadata,
                status=skill_json.get("status", "active"),
                priority=skill_json.get("priority", 0),
                agent_id=agent.id,
                enabled=True,
                gitee_repo_url=gitee_repo_url,
                gitee_commit_hash=gitee_commit_hash
            )
            session.add(skill)
            session.flush()  # 获取 skill.id
            
            # 添加 API 调用配置
            api_calls = skill_json.get("api_calls", [])
            for api_call_data in api_calls:
                api_call = SkillApiCall(
                    skill_id=skill.id,
                    api_name=api_call_data.get("name"),
                    method=api_call_data.get("method", "GET"),
                    url=api_call_data.get("url"),
                    description=api_call_data.get("description"),
                    required_params=api_call_data.get("required_params", []),
                    optional_params=api_call_data.get("optional_params", []),
                    auth_type=api_call_data.get("auth_type"),
                    auth_config=api_call_data.get("auth_config"),
                    request_headers=api_call_data.get("request_headers"),
                    request_body_template=api_call_data.get("request_body_template"),
                    response_format=api_call_data.get("response_format"),
                    timeout_seconds=api_call_data.get("timeout_seconds", 30),
                    retry_count=api_call_data.get("retry_count", 0),
                    enabled=True
                )
                session.add(api_call)
            
            # 添加依赖关系
            requirements = skill_json.get("requirements", {})
            dependencies = requirements.get("dependencies", [])
            for dep in dependencies:
                req = SkillRequirement(
                    skill_id=skill.id,
                    requirement_type="dependency",
                    requirement_name=dep,
                    is_required=True
                )
                session.add(req)
            
            api_keys = requirements.get("api_keys", [])
            for api_key in api_keys:
                req = SkillRequirement(
                    skill_id=skill.id,
                    requirement_type="api_key",
                    requirement_name=api_key,
                    is_required=True
                )
                session.add(req)
            
            min_version = requirements.get("min_agent_version")
            if min_version:
                req = SkillRequirement(
                    skill_id=skill.id,
                    requirement_type="min_version",
                    requirement_name="agent_version",
                    requirement_value=min_version,
                    is_required=True
                )
                session.add(req)
            
            session.commit()
            session.refresh(skill)
            return skill
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_skill(self, agent_name: str, name: str, description: str, content: str) -> Skill:
        """添加技能到指定角色（便捷方法，推荐使用 add_skill_from_json）
        
        注意：此方法仅用于快速测试，生产环境请使用 add_skill_from_json 方法
        从 skill-example 目录加载技能文件。
        
        Args:
            agent_name: 角色名称
            name: 技能名称
            description: 技能描述
            content: 技能详细内容
            
        Returns:
            创建的 Skill 对象
        """
        # 使用简化的 JSON 格式（自动生成 skill_id 和版本）
        skill_json = {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "description": description,
            "short_description": description[:100] if len(description) > 100 else description,
            "version": "1.0.0",
            "status": "active",
            "priority": 0
        }
        return self.add_skill_from_json(agent_name, skill_json, content)
    
    def get_skill(self, agent_name: str, skill_name: str) -> Optional[Skill]:
        """获取指定角色的技能（支持按 name 或 skill_id 查询）
        
        Args:
            agent_name: 角色名称
            skill_name: 技能名称或技能ID
            
        Returns:
            Skill 对象，如果不存在则返回 None
        """
        session = self.get_session()
        try:
            # 在同一个 session 中查询 agent
            agent = session.query(Agent).filter(
                Agent.name == agent_name,
                Agent.enabled == True
            ).first()
            
            if not agent:
                return None
            
            # 先按 skill_id 查询，如果不存在则按 name 查询
            skill = session.query(Skill).filter(
                Skill.skill_id == skill_name,
                Skill.agent_id == agent.id,
                Skill.enabled == True
            ).first()
            
            if not skill:
                skill = session.query(Skill).filter(
                    Skill.name == skill_name,
                    Skill.agent_id == agent.id,
                    Skill.enabled == True
                ).first()
            
            return skill
        finally:
            session.close()
    
    def get_skills_by_agent(self, agent_name: str) -> List[Skill]:
        """获取指定角色的所有技能
        
        Args:
            agent_name: 角色名称
            
        Returns:
            技能列表
        """
        session = self.get_session()
        try:
            # 在同一个 session 中查询 agent
            agent = session.query(Agent).filter(
                Agent.name == agent_name,
                Agent.enabled == True
            ).first()
            
            if not agent:
                return []
            
            return session.query(Skill).filter(
                Skill.agent_id == agent.id,
                Skill.enabled == True
            ).order_by(Skill.priority.desc(), Skill.name).all()
        finally:
            session.close()
    
    def get_all_skills(self, agent_name: Optional[str] = None) -> List[Dict[str, str]]:
        """获取所有技能（转换为字典格式）
        
        Args:
            agent_name: 如果指定，则只返回该角色的技能
            
        Returns:
            技能字典列表，每个包含 name, description, content
        """
        if agent_name:
            skills = self.get_skills_by_agent(agent_name)
        else:
            session = self.get_session()
            try:
                skills = session.query(Skill).filter(Skill.enabled == 'true').all()
            finally:
                session.close()
        
        return [
            {
                "name": skill.name,
                "skill_id": skill.skill_id,
                "description": skill.short_description or skill.description,
                "content": skill.content
            }
            for skill in skills
        ]
    
    # ========== API Call 相关方法 ==========
    
    def get_skill_api_calls(self, skill_id: int) -> List[SkillApiCall]:
        """获取技能的所有 API 调用配置
        
        Args:
            skill_id: 技能数据库ID
            
        Returns:
            API 调用配置列表
        """
        session = self.get_session()
        try:
            return session.query(SkillApiCall).filter(
                SkillApiCall.skill_id == skill_id,
                SkillApiCall.enabled == True
            ).all()
        finally:
            session.close()
    
    # ========== Sync Log 相关方法 ==========
    
    def add_sync_log(
        self,
        skill_id: int,
        sync_type: str,
        sync_status: str,
        sync_message: Optional[str] = None,
        gitee_commit_hash: Optional[str] = None,
        files_updated: Optional[List[str]] = None,
        sync_duration_ms: Optional[int] = None
    ) -> SkillSyncLog:
        """添加同步日志
        
        Args:
            skill_id: 技能ID
            sync_type: 同步类型（full, incremental）
            sync_status: 同步状态（success, failed, partial）
            sync_message: 同步消息或错误信息
            gitee_commit_hash: Gitee commit hash
            files_updated: 更新的文件列表
            sync_duration_ms: 同步耗时（毫秒）
            
        Returns:
            创建的同步日志对象
        """
        session = self.get_session()
        try:
            sync_log = SkillSyncLog(
                skill_id=skill_id,
                sync_type=sync_type,
                sync_status=sync_status,
                sync_message=sync_message,
                gitee_commit_hash=gitee_commit_hash,
                files_updated=files_updated,
                sync_duration_ms=sync_duration_ms
            )
            session.add(sync_log)
            session.commit()
            session.refresh(sync_log)
            return sync_log
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

