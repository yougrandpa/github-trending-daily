"""
GitHub API 客户端 - 获取 Trending 仓库信息
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import logging
from bs4 import BeautifulSoup

from config import github_config

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API 客户端"""

    def __init__(self):
        self.base_url = github_config.BASE_URL
        self.token = github_config.TOKEN
        self.max_repos = github_config.MAX_REPOSITORIES
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Trending-Bot/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """发起 HTTP 请求"""
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API 请求失败: {e}")
            return None

    def get_trending_repos(self, language: str = "", period: str = "daily") -> List[Dict]:
        """
        從 https://github.com/trending 頁面爬取真正的 trending 倉庫
        period: daily, weekly, monthly
        """
        url = "https://github.com/trending"
        if language:
            url += f"/{language.lower().replace(' ', '-')}"
        url += f"?since={period}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=12)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"無法訪問 trending 頁面: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        repos = []
        # 選擇器在 2025-2026 仍然穩定
        for article in soup.select("article.Box-row")[: self.max_repos]:
            try:
                # 名稱與連結
                a_tag = article.h2.a
                full_name = a_tag["href"].lstrip("/").strip()
                owner, name = full_name.split("/", 1)

                desc = article.select_one("p.col-9.color-fg-muted.my-1.pr-4")
                description = desc.get_text(strip=True) if desc else ""

                lang_span = article.select_one('[itemprop="programmingLanguage"]')
                language = lang_span.get_text(strip=True) if lang_span else "Unknown"

                # stars, forks
                meta = article.select("a.Link--muted")
                stars = 0
                forks = 0
                if len(meta) >= 1:
                    stars_str = meta[0].get_text(strip=True).replace(",", "")
                    stars = int(stars_str) if stars_str.isdigit() else 0
                if len(meta) >= 2:
                    forks_str = meta[1].get_text(strip=True).replace(",", "")
                    forks = int(forks_str) if forks_str.isdigit() else 0

                # 今日新增 stars（特色欄位）
                today = article.select_one("span.float-sm-right")
                today_stars_str = today.get_text(strip=True).replace("+", "").replace(",", "").split()[0] if today else "0"
                today_stars = int(today_stars_str) if today_stars_str.isdigit() else 0

                repos.append({
                    "full_name": full_name,
                    "owner": owner,
                    "name": name,
                    "url": f"https://github.com/{full_name}",
                    "description": description,
                    "language": language,
                    "stars": stars,
                    "forks": forks,
                    "today_stars": today_stars,   # 這是 trending 真正關鍵的欄位
                    # 可再加：scraped_at = datetime.utcnow().isoformat()
                })
            except Exception:
                continue  # 跳過解析失敗的單個項目

        logger.info(f"從 trending 頁面獲取到 {len(repos)} 個倉庫")
        return repos

    def get_repo_details(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取单个仓库的详细信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            仓库详细信息
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        result = self._make_request(url)

        if result:
            # 同时获取最近一次提交时间
            commits_url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            commits_result = self._make_request(commits_url, {"per_page": 1})

            last_commit = commits_result[0]["commit"]["committer"]["date"] if commits_result else None

            return {
                "stars": result.get("stargazers_count", 0),
                "forks": result.get("forks_count", 0),
                "issues": result.get("open_issues_count", 0),
                "subscribers": result.get("subscribers_count", 0),
                "size": result.get("size", 0),
                "created_at": result.get("created_at", ""),
                "pushed_at": result.get("pushed_at", ""),
                "last_commit": last_commit,
                "default_branch": result.get("default_branch", "main"),
                "topics": result.get("topics", []),
            }
        return None

    def enrich_repo_info(self, repos: List[Dict]) -> List[Dict]:
        """
        丰富仓库信息（获取额外数据）

        Args:
            repos: 仓库基本信息列表

        Returns:
            丰富后的仓库信息列表
        """
        enriched_repos = []

        for repo in repos:
            try:
                owner, name = repo["name"].split("/")
                details = self.get_repo_details(owner, name)

                if details:
                    repo.update(details)

                enriched_repos.append(repo)
                time.sleep(0.5)  # 避免 API 限流

            except Exception as e:
                logger.warning(f"获取仓库 {repo['name']} 详情失败: {e}")
                enriched_repos.append(repo)

        return enriched_repos


# 便捷函数
def get_daily_trending(language: str = "") -> List[Dict]:
    """获取今日 Trending"""
    client = GitHubClient()
    return client.get_trending_repos(language=language, period="daily")


def get_weekly_trending(language: str = "") -> List[Dict]:
    """获取本周 Trending"""
    client = GitHubClient()
    return client.get_trending_repos(language=language, period="weekly")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    client = GitHubClient()
    repos = client.get_trending_repos(days=1)

    for repo in repos[:3]:
        print(f"📦 {repo['name']}")
        print(f"   ⭐ {repo['stars']} | 🍴 {repo['forks']}")
        print(f"   {repo['description'][:100]}...")
        print()
