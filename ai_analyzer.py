"""
AI 分析模块 - 为 GitHub 仓库生成智能解读
支持自定义 API 地址，可以对接 OpenAI、Claude 或其他兼容 API
"""

import json
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

from config import ai_config

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI 仓库分析器"""

    def __init__(self):
        self.base_url = ai_config.BASE_URL
        self.api_key = ai_config.API_KEY
        self.model = ai_config.MODEL
        self.timeout = ai_config.TIMEOUT
        self.max_retries = ai_config.MAX_RETRIES
        self.temperature = ai_config.TEMPERATURE
        self.system_prompt = ai_config.SYSTEM_PROMPT
        self.user_prompt_template = ai_config.USER_PROMPT_TEMPLATE

    def _make_api_request(self, messages: List[Dict], stream: bool = False) -> Optional[str]:
        """
        调用 AI API

        Args:
            messages: 消息列表
            stream: 是否使用流式响应

        Returns:
            AI 生成的文本内容
        """
        if not self.base_url or not self.api_key:
            logger.error("AI API 配置不完整（BASE_URL 或 API_KEY 未设置）")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 2000
        }

        if stream:
            payload["stream"] = True

        # 尝试不同的 API 端点格式
        endpoints = [
            f"{self.base_url}/chat/completions",
            f"{self.base_url}/completions",
        ]

        for endpoint in endpoints:
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"尝试 API 端点: {endpoint}")
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout,
                        stream=stream
                    )
                    response.raise_for_status()

                    if stream:
                        return self._handle_stream_response(response)
                    else:
                        result = response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            return result["choices"][0]["message"]["content"]
                        elif "completion" in result:
                            return result["completion"]
                        else:
                            logger.error(f"API 响应格式异常: {result}")
                            return None

                except requests.exceptions.RequestException as e:
                    logger.warning(f"API 请求失败（尝试 {attempt + 1}/{self.max_retries}）: {e}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # 指数退避
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失败: {e}")
                    continue

            # 如果所有端点都失败
            if endpoint != endpoints[-1]:
                continue
            else:
                logger.error("所有 API 端点均失败")
                return None

        return None

    def _handle_stream_response(self, response) -> str:
        """处理流式响应"""
        content = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        json_data = json.loads(data)
                        if 'choices' in json_data:
                            delta = json_data['choices'][0].get('delta', {})
                            content += delta.get('content', '')
                    except json.JSONDecodeError:
                        continue
        return content

    def analyze_repo(self, repo: Dict) -> Dict:
        """
        分析单个仓库

        Args:
            repo: 仓库信息字典

        Returns:
            包含 AI 分析结果的字典
        """
        # 构建用户提示词
        user_prompt = self.user_prompt_template.format(
            name=repo.get("name", ""),
            url=repo.get("url", ""),
            stars=repo.get("stars", 0),
            forks=repo.get("forks", 0),
            description=repo.get("description", ""),
            language=repo.get("language", ""),
            updated_at=repo.get("updated_at", "")
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"正在分析仓库: {repo.get('name')}")

        # 调用 AI API
        analysis = self._make_api_request(messages)

        if analysis:
            # 尝试解析为结构化数据
            try:
                # 尝试提取 JSON
                if "```json" in analysis:
                    json_start = analysis.find("```json") + 7
                    json_end = analysis.find("```", json_start)
                    if json_end > json_start:
                        analysis = analysis[json_start:json_end].strip()
                        structured = json.loads(analysis)
                        analysis = structured
            except Exception as e:
                logger.debug(f"解析结构化数据失败，使用原始文本: {e}")

            return {
                "name": repo.get("name"),
                "url": repo.get("url"),
                "analysis": analysis,
                "success": True
            }
        else:
            # 如果 AI 调用失败，返回基本信息
            logger.warning(f"AI 分析失败，返回基本信息: {repo.get('name')}")
            return {
                "name": repo.get("name"),
                "url": repo.get("url"),
                "analysis": "（AI 分析暂时不可用）",
                "success": False
            }

    def analyze_repos_batch(self, repos: List[Dict], delay: float = 1.0) -> List[Dict]:
        """
        批量分析仓库

        Args:
            repos: 仓库列表
            delay: 每次请求之间的延迟（秒）

        Returns:
            分析结果列表
        """
        results = []
        total = len(repos)

        for i, repo in enumerate(repos):
            logger.info(f"正在分析 {i+1}/{total}: {repo.get('name')}")

            result = self.analyze_repo(repo)
            results.append(result)

            # 添加延迟以避免 API 限流
            if i < total - 1:
                import time
                time.sleep(delay)

        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"分析完成: {success_count}/{total} 成功")

        return results


# 便捷函数
def analyze_repositories(repos: List[Dict]) -> List[Dict]:
    """分析仓库列表"""
    analyzer = AIAnalyzer()
    return analyzer.analyze_repos_batch(repos)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试提示词
    analyzer = AIAnalyzer()
    test_repo = {
        "name": "zustand-js/zustand",
        "url": "https://github.com/zustand-js/zustand",
        "stars": 35000,
        "forks": 1500,
        "description": "A small, fast and scalable bearbones state-management solution using simplified flux principles.",
        "language": "TypeScript",
        "updated_at": "2024-01-15T10:30:00Z"
    }

    print("测试 AI 分析功能...")
    result = analyzer.analyze_repo(test_repo)
    print(f"\n仓库: {result['name']}")
    print(f"分析结果:\n{result['analysis']}")
