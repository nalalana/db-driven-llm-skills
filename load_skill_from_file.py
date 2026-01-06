"""
从 skill-example 文件夹加载技能的工具函数
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple


def load_skill_from_directory(skill_dir: str) -> Tuple[Dict, str, Optional[Dict], Optional[Dict]]:
    """从技能目录加载技能文件
    
    Args:
        skill_dir: 技能目录路径（例如：skill-example/data_analysis）
        
    Returns:
        (skill_json, content, examples, metadata) 元组
    """
    skill_path = Path(skill_dir)
    
    # 加载 skill.json
    skill_json_path = skill_path / "skill.json"
    if not skill_json_path.exists():
        raise FileNotFoundError(f"skill.json 不存在: {skill_json_path}")
    
    with open(skill_json_path, 'r', encoding='utf-8') as f:
        skill_json = json.load(f)
    
    # 加载 content.md
    content_file = skill_json.get("content_file", "content.md")
    content_path = skill_path / content_file
    if not content_path.exists():
        raise FileNotFoundError(f"内容文件不存在: {content_path}")
    
    with open(content_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 加载 examples.json（可选）
    examples = None
    examples_file = skill_json.get("examples_file")
    if examples_file:
        examples_path = skill_path / examples_file
        if examples_path.exists():
            with open(examples_path, 'r', encoding='utf-8') as f:
                examples = json.load(f)
    
    # 加载 metadata.json（可选）
    metadata = None
    metadata_path = skill_path / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    return skill_json, content, examples, metadata


def load_all_skills_from_example_dir(example_dir: str = "skill-example") -> Dict[str, Tuple[Dict, str, Optional[Dict], Optional[Dict]]]:
    """从 skill-example 目录加载所有技能
    
    Args:
        example_dir: skill-example 目录路径
        
    Returns:
        字典，key 为技能目录名，value 为 (skill_json, content, examples, metadata) 元组
    """
    skills = {}
    example_path = Path(example_dir)
    
    if not example_path.exists():
        return skills
    
    # 遍历所有子目录
    for skill_dir in example_path.iterdir():
        if skill_dir.is_dir() and (skill_dir / "skill.json").exists():
            try:
                skill_data = load_skill_from_directory(str(skill_dir))
                skills[skill_dir.name] = skill_data
            except Exception as e:
                print(f"警告: 加载技能 {skill_dir.name} 失败: {str(e)}")
    
    return skills

