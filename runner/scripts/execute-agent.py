#!/usr/bin/env python3

"""
AutoCodit Agent Executor

Main agent execution logic that orchestrates AI models,
MCP servers, and code operations.
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add the workspace to Python path
sys.path.insert(0, '/workspace')

# Agent configuration
CONFIG = {
    "session_id": os.environ["SESSION_ID"],
    "task_id": os.environ["TASK_ID"],
    "repository_url": os.environ["REPOSITORY_URL"],
    "task_description": os.environ["TASK_DESCRIPTION"],
    "action_type": os.environ["ACTION_TYPE"],
    "api_endpoint": os.environ.get("API_ENDPOINT", "http://api:8000"),
    "mcp_port": int(os.environ.get("MCP_SERVER_PORT", "2301")),
    "github_token": os.environ.get("GITHUB_INSTALLATION_TOKEN", ""),
    "agent_config": json.loads(os.environ.get("AGENT_CONFIG", "{}")),
    "workspace_dir": "/workspace",
    "repo_dir": "/workspace/repository",
    "agent_home": os.environ.get("AGENT_HOME", "/home/agent/.autocodit")
}


class AgentExecutor:
    """Main agent executor class"""
    
    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.mcp_client = None
        self.ai_client = None
        self.github_client = None
        self.workspace_dir = Path(self.config["workspace_dir"])
        self.repo_dir = Path(self.config["repo_dir"])
        
    def log(self, level: str, message: str, **kwargs):
        """Structured logging"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "component": "agent-executor",
            "session_id": self.config["session_id"],
            "task_id": self.config["task_id"],
            **kwargs
        }
        
        print(json.dumps(log_entry), flush=True)
    
    async def initialize(self):
        """Initialize agent components"""
        self.log("INFO", "Initializing agent executor")
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Initialize MCP client
        await self.initialize_mcp_client()
        
        # Initialize AI client
        await self.initialize_ai_client()
        
        # Initialize GitHub client
        await self.initialize_github_client()
        
        self.log("INFO", "Agent initialization completed")
    
    async def initialize_mcp_client(self):
        """Initialize MCP client connection"""
        mcp_url = f"http://localhost:{self.config['mcp_port']}"
        
        # Test MCP connection
        for attempt in range(30):
            try:
                async with self.session.get(f"{mcp_url}/health") as response:
                    if response.status == 200:
                        self.mcp_client = MCPClient(mcp_url, self.session)
                        self.log("INFO", "MCP client connected")
                        return
            except Exception:
                pass
            
            await asyncio.sleep(2)
        
        raise Exception("Failed to connect to MCP server")
    
    async def initialize_ai_client(self):
        """Initialize AI client"""
        self.ai_client = AIClient(
            api_endpoint=self.config["api_endpoint"],
            session=self.session
        )
        
        self.log("INFO", "AI client initialized")
    
    async def initialize_github_client(self):
        """Initialize GitHub client"""
        self.github_client = GitHubClient(
            token=self.config["github_token"],
            session=self.session
        )
        
        self.log("INFO", "GitHub client initialized")
    
    async def execute_task(self):
        """Execute the main task"""
        action_type = self.config["action_type"]
        description = self.config["task_description"]
        
        self.log("INFO", f"Starting task execution: {action_type}", description=description)
        
        try:
            # Update task status
            await self.update_task_status("running", 0.1, "Analyzing repository...")
            
            # Analyze repository
            analysis = await self.analyze_repository()
            
            # Create execution plan
            await self.update_task_status("running", 0.2, "Creating execution plan...")
            plan = await self.create_execution_plan(analysis, description)
            
            # Execute plan steps
            results = await self.execute_plan(plan)
            
            # Validate results
            await self.update_task_status("running", 0.9, "Validating results...")
            validation = await self.validate_results(results)
            
            if validation["success"]:
                # Create commit and branch
                commit_result = await self.create_commit(results)
                
                await self.update_task_status("completed", 1.0, "Task completed successfully")
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "plan": plan,
                    "results": results,
                    "validation": validation,
                    "commit": commit_result
                }
            else:
                await self.update_task_status("failed", None, "Validation failed")
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation": validation
                }
        
        except Exception as e:
            self.log("ERROR", f"Task execution failed: {str(e)}")
            await self.update_task_status("failed", None, f"Execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_repository(self) -> Dict[str, Any]:
        """Analyze repository structure and context"""
        self.log("INFO", "Starting repository analysis")
        
        # Use MCP to analyze repository
        file_list = await self.mcp_client.list_files()
        
        # Get recent commits
        recent_commits = await self.github_client.get_recent_commits(limit=10)
        
        # Analyze code structure
        structure_analysis = await self.mcp_client.analyze_structure()
        
        # Search for relevant files based on task description
        relevant_files = await self.mcp_client.search_relevant_files(
            self.config["task_description"]
        )
        
        analysis = {
            "file_count": len(file_list),
            "file_types": self._categorize_files(file_list),
            "recent_commits": recent_commits,
            "structure": structure_analysis,
            "relevant_files": relevant_files,
            "has_tests": self._has_tests(file_list),
            "has_ci": self._has_ci_config(file_list),
            "languages": self._detect_languages(file_list)
        }
        
        self.log("INFO", "Repository analysis completed", 
                file_count=analysis["file_count"],
                languages=analysis["languages"])
        
        return analysis
    
    async def create_execution_plan(self, analysis: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Create detailed execution plan using AI"""
        self.log("INFO", "Creating execution plan")
        
        # Prepare context for AI
        context = {
            "task_description": description,
            "action_type": self.config["action_type"],
            "repository_analysis": analysis,
            "relevant_files": analysis["relevant_files"]
        }
        
        # Get AI-generated plan
        plan_response = await self.ai_client.create_plan(context)
        
        plan = {
            "steps": plan_response["steps"],
            "estimated_time": plan_response.get("estimated_time", 1800),
            "files_to_modify": plan_response.get("files_to_modify", []),
            "tests_to_run": plan_response.get("tests_to_run", []),
            "validation_steps": plan_response.get("validation_steps", [])
        }
        
        self.log("INFO", "Execution plan created", 
                steps_count=len(plan["steps"]),
                estimated_time=plan["estimated_time"])
        
        return plan
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plan steps"""
        self.log("INFO", "Starting plan execution")
        
        results = {
            "steps_completed": [],
            "files_modified": [],
            "tests_results": [],
            "errors": []
        }
        
        total_steps = len(plan["steps"])
        
        for i, step in enumerate(plan["steps"]):
            step_progress = 0.3 + (0.6 * (i + 1) / total_steps)  # 30% to 90%
            
            await self.update_task_status(
                "running", 
                step_progress, 
                f"Executing step {i+1}/{total_steps}: {step['description']}"
            )
            
            try:
                step_result = await self.execute_step(step)
                results["steps_completed"].append({
                    "step": step,
                    "result": step_result,
                    "success": True
                })
                
            except Exception as e:
                error_msg = f"Step {i+1} failed: {str(e)}"
                self.log("ERROR", error_msg, step=step)
                
                results["errors"].append({
                    "step": step,
                    "error": str(e)
                })
                
                # Decide whether to continue or abort
                if step.get("critical", True):
                    raise Exception(error_msg)
        
        return results
    
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single plan step"""
        step_type = step.get("type")
        
        if step_type == "modify_file":
            return await self.modify_file(step)
        elif step_type == "create_file":
            return await self.create_file(step)
        elif step_type == "run_tests":
            return await self.run_tests(step)
        elif step_type == "run_command":
            return await self.run_command(step)
        else:
            raise Exception(f"Unknown step type: {step_type}")
    
    async def modify_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing file"""
        file_path = step["file_path"]
        modifications = step["modifications"]
        
        self.log("INFO", f"Modifying file: {file_path}")
        
        # Read current file content
        current_content = await self.mcp_client.read_file(file_path)
        
        # Apply modifications using AI
        new_content = await self.ai_client.apply_modifications(
            current_content, modifications
        )
        
        # Write modified content
        await self.mcp_client.write_file(file_path, new_content)
        
        return {
            "file_path": file_path,
            "modifications_applied": len(modifications),
            "content_length": len(new_content)
        }
    
    async def create_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file"""
        file_path = step["file_path"]
        content = step["content"]
        
        self.log("INFO", f"Creating file: {file_path}")
        
        # Generate content using AI if not provided
        if not content:
            content = await self.ai_client.generate_file_content(
                file_path, step.get("requirements", "")
            )
        
        # Write file
        await self.mcp_client.write_file(file_path, content)
        
        return {
            "file_path": file_path,
            "content_length": len(content)
        }
    
    async def run_tests(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Run test suite"""
        test_command = step.get("command", "npm test")
        
        self.log("INFO", f"Running tests: {test_command}")
        
        # Execute test command via MCP
        result = await self.mcp_client.execute_command(test_command)
        
        return {
            "command": test_command,
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "success": result["exit_code"] == 0
        }
    
    async def run_command(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Run arbitrary command"""
        command = step["command"]
        
        self.log("INFO", f"Running command: {command}")
        
        result = await self.mcp_client.execute_command(command)
        
        return {
            "command": command,
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "success": result["exit_code"] == 0
        }
    
    async def validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution results"""
        self.log("INFO", "Validating execution results")
        
        validation = {
            "success": True,
            "checks": [],
            "warnings": [],
            "errors": []
        }
        
        # Check if all critical steps completed
        if results["errors"]:
            validation["success"] = False
            validation["errors"].extend(results["errors"])
        
        # Run tests if available
        if self._has_tests_available():
            test_result = await self.run_tests({
                "command": self._detect_test_command()
            })
            
            validation["checks"].append({
                "name": "test_suite",
                "success": test_result["success"],
                "details": test_result
            })
            
            if not test_result["success"]:
                validation["success"] = False
                validation["errors"].append("Test suite failed")
        
        # Validate syntax for modified files
        for file_info in results["files_modified"]:
            syntax_check = await self._validate_file_syntax(file_info["file_path"])
            
            validation["checks"].append({
                "name": f"syntax_{file_info['file_path']}",
                "success": syntax_check["valid"],
                "details": syntax_check
            })
            
            if not syntax_check["valid"]:
                validation["success"] = False
                validation["errors"].append(f"Syntax error in {file_info['file_path']}")
        
        self.log("INFO", "Validation completed", 
                success=validation["success"],
                checks=len(validation["checks"]),
                errors=len(validation["errors"]))
        
        return validation
    
    async def create_commit(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create commit with changes"""
        action_type = self.config["action_type"]
        task_id = self.config["task_id"][:8]
        
        # Generate commit message
        commit_message = await self.ai_client.generate_commit_message(
            action_type=action_type,
            description=self.config["task_description"],
            files_modified=[f["file_path"] for f in results["files_modified"]]
        )
        
        # Create branch name
        branch_name = f"autocodit/{action_type}-{task_id}"
        
        # Create and push changes via MCP
        commit_result = await self.mcp_client.create_commit(
            branch_name=branch_name,
            commit_message=commit_message,
            files=results["files_modified"]
        )
        
        self.log("INFO", "Commit created", 
                branch_name=branch_name,
                commit_sha=commit_result["sha"])
        
        return {
            "branch_name": branch_name,
            "commit_message": commit_message,
            "commit_sha": commit_result["sha"],
            "files_changed": len(results["files_modified"])
        }
    
    async def update_task_status(self, status: str, progress: Optional[float], message: str):
        """Update task status via API"""
        try:
            async with self.session.post(
                f"{self.config['api_endpoint']}/api/v1/tasks/{self.config['task_id']}/status",
                json={
                    "status": status,
                    "progress": progress,
                    "message": message
                }
            ) as response:
                if response.status == 200:
                    self.log("DEBUG", "Task status updated", status=status, progress=progress)
                else:
                    self.log("WARNING", "Failed to update task status", status_code=response.status)
        
        except Exception as e:
            self.log("WARNING", f"Failed to update task status: {str(e)}")
    
    def _has_tests_available(self) -> bool:
        """Check if tests are available"""
        test_dirs = ["tests", "test", "__tests__", "src/test"]
        return any((self.repo_dir / test_dir).exists() for test_dir in test_dirs)
    
    def _detect_test_command(self) -> str:
        """Detect appropriate test command"""
        if (self.repo_dir / "package.json").exists():
            return "npm test"
        elif (self.repo_dir / "pytest.ini").exists() or (self.repo_dir / "pyproject.toml").exists():
            return "python -m pytest"
        elif (self.repo_dir / "go.mod").exists():
            return "go test ./..."
        else:
            return "echo 'No test command detected'"
    
    async def _validate_file_syntax(self, file_path: str) -> Dict[str, Any]:
        """Validate file syntax"""
        # Use MCP to validate syntax
        return await self.mcp_client.validate_syntax(file_path)
    
    def _categorize_files(self, file_list: List[str]) -> Dict[str, int]:
        """Categorize files by type"""
        categories = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "java": 0,
            "go": 0,
            "other": 0
        }
        
        for file_path in file_list:
            if file_path.endswith('.py'):
                categories["python"] += 1
            elif file_path.endswith(('.js', '.jsx')):
                categories["javascript"] += 1
            elif file_path.endswith(('.ts', '.tsx')):
                categories["typescript"] += 1
            elif file_path.endswith('.java'):
                categories["java"] += 1
            elif file_path.endswith('.go'):
                categories["go"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _has_tests(self, file_list: List[str]) -> bool:
        """Check if repository has tests"""
        return any(
            "test" in file_path.lower() or "spec" in file_path.lower()
            for file_path in file_list
        )
    
    def _has_ci_config(self, file_list: List[str]) -> bool:
        """Check if repository has CI configuration"""
        ci_files = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"]
        return any(ci_file in file_path for ci_file in ci_files for file_path in file_list)
    
    def _detect_languages(self, file_list: List[str]) -> List[str]:
        """Detect programming languages"""
        extensions = set()
        for file_path in file_list:
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                extensions.add(ext)
        
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'jsx': 'React',
            'tsx': 'React TypeScript',
            'java': 'Java',
            'go': 'Go',
            'rs': 'Rust',
            'cpp': 'C++',
            'c': 'C',
            'php': 'PHP',
            'rb': 'Ruby',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala'
        }
        
        return [language_map.get(ext, ext.title()) for ext in extensions if ext in language_map]
    
    async def cleanup(self):
        """Cleanup resources"""
        self.log("INFO", "Cleaning up agent resources")
        
        if self.session:
            await self.session.close()
        
        self.log("INFO", "Agent cleanup completed")


class MCPClient:
    """Model Context Protocol client"""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
    
    async def list_files(self, path: str = ".") -> List[str]:
        """List files in repository"""
        async with self.session.post(
            f"{self.base_url}/tools/list_files",
            json={"path": path}
        ) as response:
            result = await response.json()
            return result.get("files", [])
    
    async def read_file(self, file_path: str) -> str:
        """Read file content"""
        async with self.session.post(
            f"{self.base_url}/tools/read_file",
            json={"file_path": file_path}
        ) as response:
            result = await response.json()
            return result.get("content", "")
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write file content"""
        async with self.session.post(
            f"{self.base_url}/tools/write_file",
            json={"file_path": file_path, "content": content}
        ) as response:
            return await response.json()
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command"""
        async with self.session.post(
            f"{self.base_url}/tools/execute_command",
            json={"command": command}
        ) as response:
            return await response.json()
    
    async def create_commit(self, branch_name: str, commit_message: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create commit with changes"""
        async with self.session.post(
            f"{self.base_url}/tools/create_commit",
            json={
                "branch_name": branch_name,
                "commit_message": commit_message,
                "files": files
            }
        ) as response:
            return await response.json()


class AIClient:
    """AI client for agent operations"""
    
    def __init__(self, api_endpoint: str, session: aiohttp.ClientSession):
        self.api_endpoint = api_endpoint
        self.session = session
    
    async def create_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution plan"""
        async with self.session.post(
            f"{self.api_endpoint}/api/v1/ai/plan",
            json=context
        ) as response:
            return await response.json()
    
    async def apply_modifications(self, content: str, modifications: List[Dict[str, Any]]) -> str:
        """Apply modifications to content"""
        async with self.session.post(
            f"{self.api_endpoint}/api/v1/ai/modify",
            json={"content": content, "modifications": modifications}
        ) as response:
            result = await response.json()
            return result.get("modified_content", content)


class GitHubClient:
    """GitHub API client"""
    
    def __init__(self, token: str, session: aiohttp.ClientSession):
        self.token = token
        self.session = session
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_recent_commits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits"""
        repo_info = CONFIG["repository_url"].split("/")[-2:]
        owner, repo = repo_info[0], repo_info[1].replace(".git", "")
        
        async with self.session.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits",
            headers=self.headers,
            params={"per_page": limit}
        ) as response:
            if response.status == 200:
                return await response.json()
            return []


# Main execution
async def main():
    """Main execution function"""
    executor = AgentExecutor()
    
    try:
        await executor.initialize()
        result = await executor.execute_task()
        
        executor.log("INFO", "Agent execution completed", success=result["success"])
        
        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)
    
    except Exception as e:
        executor.log("ERROR", f"Agent execution failed: {str(e)}")
        sys.exit(1)
    
    finally:
        await executor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())