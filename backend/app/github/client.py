"""
AutoCodit Agent - GitHub API Client

Authenticated GitHub API client for GitHub App integration.
Handles JWT token generation and installation token management.
"""

import time
from typing import Optional, Dict, Any, List
import jwt
from github import Github, GithubIntegration
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class GitHubClient:
    """GitHub API client with App authentication"""
    
    def __init__(self):
        self.settings = get_settings()
        self._integration = None
        self._installation_tokens: Dict[int, Dict[str, Any]] = {}
    
    @property
    def integration(self) -> GithubIntegration:
        """Get GitHub integration instance"""
        if not self._integration:
            self._integration = GithubIntegration(
                self.settings.GITHUB_APP_ID,
                self.settings.GITHUB_PRIVATE_KEY,
                base_url=self.settings.GITHUB_API_URL
            )
        return self._integration
    
    def generate_jwt_token(self) -> str:
        """Generate JWT token for GitHub App authentication"""
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + 540,  # 9 minutes (max 10 minutes)
            "iss": self.settings.GITHUB_APP_ID
        }
        
        return jwt.encode(
            payload,
            self.settings.GITHUB_PRIVATE_KEY,
            algorithm="RS256"
        )
    
    async def get_installation_token(self, installation_id: int) -> str:
        """Get installation access token (cached)"""
        now = int(time.time())
        
        # Check if we have a valid cached token
        if installation_id in self._installation_tokens:
            token_data = self._installation_tokens[installation_id]
            if token_data["expires_at"] > now + 60:  # 1 minute buffer
                return token_data["token"]
        
        # Get new installation token
        try:
            token_response = self.integration.get_access_token(installation_id)
            
            # Cache token
            self._installation_tokens[installation_id] = {
                "token": token_response.token,
                "expires_at": int(token_response.expires_at.timestamp())
            }
            
            logger.info(
                "Generated new installation token",
                installation_id=installation_id,
                expires_at=token_response.expires_at
            )
            
            return token_response.token
        
        except Exception as e:
            logger.error(
                "Failed to get installation token",
                installation_id=installation_id,
                error=str(e)
            )
            raise
    
    async def get_github_client(self, installation_id: int) -> Github:
        """Get authenticated GitHub client for installation"""
        token = await self.get_installation_token(installation_id)
        return Github(token, base_url=self.settings.GITHUB_API_URL)
    
    async def get_installations(self) -> List[Dict[str, Any]]:
        """Get all installations for this GitHub App"""
        try:
            installations = self.integration.get_installations()
            return [
                {
                    "id": installation.id,
                    "account": {
                        "login": installation.account.login,
                        "type": installation.account.type,
                        "id": installation.account.id
                    },
                    "permissions": installation.permissions,
                    "repository_selection": installation.repository_selection
                }
                for installation in installations
            ]
        
        except Exception as e:
            logger.error("Failed to get installations", error=str(e))
            raise
    
    async def get_installation_repositories(
        self,
        installation_id: int
    ) -> List[Dict[str, Any]]:
        """Get repositories accessible by installation"""
        try:
            github_client = await self.get_github_client(installation_id)
            repos = github_client.get_installation(installation_id).get_repos()
            
            return [
                {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "default_branch": repo.default_branch,
                    "permissions": {
                        "admin": repo.permissions.admin,
                        "push": repo.permissions.push,
                        "pull": repo.permissions.pull
                    }
                }
                for repo in repos
            ]
        
        except Exception as e:
            logger.error(
                "Failed to get installation repositories",
                installation_id=installation_id,
                error=str(e)
            )
            raise
    
    async def create_issue_comment(
        self,
        installation_id: int,
        repo_full_name: str,
        issue_number: int,
        comment_body: str
    ) -> Dict[str, Any]:
        """Create comment on issue or PR"""
        try:
            github_client = await self.get_github_client(installation_id)
            repo = github_client.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            
            comment = issue.create_comment(comment_body)
            
            logger.info(
                "Created issue comment",
                repository=repo_full_name,
                issue_number=issue_number,
                comment_id=comment.id
            )
            
            return {
                "id": comment.id,
                "body": comment.body,
                "created_at": comment.created_at,
                "html_url": comment.html_url
            }
        
        except Exception as e:
            logger.error(
                "Failed to create issue comment",
                repository=repo_full_name,
                issue_number=issue_number,
                error=str(e)
            )
            raise
    
    async def create_pull_request(
        self,
        installation_id: int,
        repo_full_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = True
    ) -> Dict[str, Any]:
        """Create pull request"""
        try:
            github_client = await self.get_github_client(installation_id)
            repo = github_client.get_repo(repo_full_name)
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft
            )
            
            logger.info(
                "Created pull request",
                repository=repo_full_name,
                pr_number=pr.number,
                title=title
            )
            
            return {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "html_url": pr.html_url,
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha
                },
                "draft": pr.draft,
                "state": pr.state
            }
        
        except Exception as e:
            logger.error(
                "Failed to create pull request",
                repository=repo_full_name,
                title=title,
                error=str(e)
            )
            raise
    
    async def create_check_run(
        self,
        installation_id: int,
        repo_full_name: str,
        commit_sha: str,
        name: str,
        status: str = "in_progress",
        conclusion: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create check run for commit"""
        try:
            github_client = await self.get_github_client(installation_id)
            repo = github_client.get_repo(repo_full_name)
            
            check_run_data = {
                "name": name,
                "head_sha": commit_sha,
                "status": status
            }
            
            if conclusion:
                check_run_data["conclusion"] = conclusion
            
            if output:
                check_run_data["output"] = output
            
            check_run = repo.create_check_run(**check_run_data)
            
            logger.info(
                "Created check run",
                repository=repo_full_name,
                commit_sha=commit_sha,
                check_run_id=check_run.id,
                name=name
            )
            
            return {
                "id": check_run.id,
                "name": check_run.name,
                "status": check_run.status,
                "conclusion": check_run.conclusion,
                "html_url": check_run.html_url
            }
        
        except Exception as e:
            logger.error(
                "Failed to create check run",
                repository=repo_full_name,
                commit_sha=commit_sha,
                name=name,
                error=str(e)
            )
            raise


# Global GitHub client instance
github_client = GitHubClient()