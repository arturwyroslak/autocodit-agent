import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ..models.task import Task, TaskStatus
from ..models.session import Session, SessionStatus
from ..services.ai_service import ai_orchestrator
from ..services.github_service import GitHubService
from ..services.runner_service import RunnerService
from ..core.config import get_settings
from ..core.database import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery app
celery_app = Celery('autocodit_agent')
celery_app.config_from_object(settings, namespace='CELERY')

# Database setup for workers
engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession)


class AgentExecutor:
    """Main agent executor for coding tasks"""
    
    def __init__(self):
        self.ai_service = ai_orchestrator
        self.github_service = GitHubService()
        self.runner_service = RunnerService()
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a coding task end-to-end"""
        
        async with SessionLocal() as db:
            try:
                # Get task from database
                task = await db.get(Task, task_id)
                if not task:
                    raise ValueError(f"Task {task_id} not found")
                
                # Update task status to running
                task.status = TaskStatus.RUNNING
                await db.commit()
                
                logger.info(f"Starting execution of task {task_id}: {task.title}")
                
                # Create execution session
                session = await self.runner_service.create_session(task, db)
                
                # Phase 1: Analysis and Planning
                plan = await self._analyze_and_plan(task, session, db)
                
                # Phase 2: Code Generation and Modification
                results = await self._execute_plan(task, session, plan, db)
                
                # Phase 3: Validation and Testing
                validation = await self._validate_results(task, session, results, db)
                
                # Phase 4: Commit and PR Creation
                if validation['success']:
                    pr_result = await self._create_pull_request(task, session, results, db)
                    
                    # Update task status to completed
                    task.status = TaskStatus.COMPLETED
                    task.result_summary = f"Successfully created PR #{pr_result.get('number')}"
                    task.files_changed = results.get('files_modified', [])
                    task.commits_created = results.get('commits', [])
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = validation.get('error', 'Validation failed')
                
                # Update session
                session.status = SessionStatus.COMPLETED if validation['success'] else SessionStatus.FAILED
                session.completed_at = datetime.now(timezone.utc)
                
                await db.commit()
                
                return {
                    'success': validation['success'],
                    'task_id': task_id,
                    'session_id': session.id,
                    'results': results,
                    'validation': validation,
                    'pr_result': pr_result if validation['success'] else None
                }
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                
                # Update task status to failed
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await db.commit()
                
                raise
    
    async def _analyze_and_plan(self, task: Task, session: Session, db: AsyncSession) -> Dict[str, Any]:
        """Analyze the repository and create execution plan"""
        
        logger.info(f"Analyzing task {task.id}")
        
        # Update session status
        session.status = SessionStatus.PLANNING
        await db.commit()
        
        # Get repository context
        repo_context = await self.github_service.get_repository_context(
            task.repository.full_name,
            task.base_branch
        )
        
        # Analyze issue or PR context if available
        issue_context = None
        if task.issue_number:
            issue_context = await self.github_service.get_issue_context(
                task.repository.full_name,
                task.issue_number
            )
        
        # Create AI planning prompt
        planning_messages = [
            {
                "role": "system",
                "content": self._get_planning_system_prompt()
            },
            {
                "role": "user",
                "content": self._format_planning_request(
                    task, repo_context, issue_context
                )
            }
        ]
        
        # Get AI plan
        ai_response = await self.ai_service.generate_completion(
            messages=planning_messages,
            model_preference=task.agent_config.model_primary if task.agent_config else None,
            session_id=session.id
        )
        
        # Parse plan from AI response
        plan = self._parse_ai_plan(ai_response.content)
        
        # Update session with plan
        session.plan = plan
        session.total_steps = len(plan.get('steps', []))
        await db.commit()
        
        logger.info(f"Created plan with {session.total_steps} steps for task {task.id}")
        
        return plan
    
    async def _execute_plan(self, task: Task, session: Session, plan: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Execute the generated plan"""
        
        logger.info(f"Executing plan for task {task.id}")
        
        # Update session status
        session.status = SessionStatus.EXECUTING
        await db.commit()
        
        results = {
            'files_modified': [],
            'commits': [],
            'tests_run': [],
            'errors': []
        }
        
        steps = plan.get('steps', [])
        
        for i, step in enumerate(steps):
            try:
                logger.info(f"Executing step {i+1}/{len(steps)}: {step.get('description')}")
                
                # Update session progress
                session.current_step = i + 1
                await db.commit()
                
                # Execute step based on type
                step_result = await self._execute_step(task, session, step, db)
                
                # Collect results
                if step_result.get('files_modified'):
                    results['files_modified'].extend(step_result['files_modified'])
                
                if step_result.get('error'):
                    results['errors'].append({
                        'step': i + 1,
                        'error': step_result['error']
                    })
                    
                    # Decide if we should continue or abort
                    if step.get('critical', True):
                        raise Exception(f"Critical step failed: {step_result['error']}")
                
            except Exception as e:
                logger.error(f"Step {i+1} failed: {e}")
                results['errors'].append({
                    'step': i + 1,
                    'error': str(e)
                })
                
                if step.get('critical', True):
                    raise
        
        logger.info(f"Plan execution completed for task {task.id}")
        
        return results
    
    async def _execute_step(self, task: Task, session: Session, step: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Execute a single plan step"""
        
        step_type = step.get('type')
        
        if step_type == 'modify_file':
            return await self._modify_file(task, step)
        elif step_type == 'create_file':
            return await self._create_file(task, step)
        elif step_type == 'run_tests':
            return await self._run_tests(task, step)
        elif step_type == 'run_command':
            return await self._run_command(task, step)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    async def _validate_results(self, task: Task, session: Session, results: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Validate the execution results"""
        
        logger.info(f"Validating results for task {task.id}")
        
        # Update session status
        session.status = SessionStatus.VALIDATING
        await db.commit()
        
        validation = {
            'success': True,
            'checks': [],
            'warnings': [],
            'errors': []
        }
        
        # Check if there were any critical errors
        if results.get('errors'):
            critical_errors = [e for e in results['errors'] if e.get('critical', True)]
            if critical_errors:
                validation['success'] = False
                validation['errors'].extend([e['error'] for e in critical_errors])
        
        # Run tests if configured
        if task.agent_config and task.agent_config.run_tests:
            test_result = await self._run_validation_tests(task)
            validation['checks'].append({
                'name': 'tests',
                'success': test_result.get('success', False),
                'details': test_result
            })
            
            if not test_result.get('success', False):
                validation['success'] = False
                validation['errors'].append('Tests failed')
        
        # Validate syntax if files were modified
        if results.get('files_modified'):
            syntax_validation = await self._validate_syntax(results['files_modified'])
            validation['checks'].append({
                'name': 'syntax',
                'success': syntax_validation.get('success', True),
                'details': syntax_validation
            })
            
            if not syntax_validation.get('success', True):
                validation['success'] = False
                validation['errors'].extend(syntax_validation.get('errors', []))
        
        logger.info(f"Validation {'passed' if validation['success'] else 'failed'} for task {task.id}")
        
        return validation
    
    async def _create_pull_request(self, task: Task, session: Session, results: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Create pull request with the changes"""
        
        logger.info(f"Creating pull request for task {task.id}")
        
        # Create branch name
        branch_name = f"autocodit/task-{task.id[:8]}"
        
        # Generate commit message
        commit_message = self._generate_commit_message(task, results)
        
        # Generate PR description
        pr_description = self._generate_pr_description(task, results)
        
        # Create branch and commit changes
        commit_result = await self.github_service.create_branch_and_commit(
            task.repository.full_name,
            branch_name,
            task.base_branch,
            results['files_modified'],
            commit_message
        )
        
        # Create pull request
        pr_result = await self.github_service.create_pull_request(
            task.repository.full_name,
            title=f"AutoCodit: {task.title}",
            body=pr_description,
            head=branch_name,
            base=task.base_branch
        )
        
        logger.info(f"Created PR #{pr_result['number']} for task {task.id}")
        
        return pr_result
    
    def _get_planning_system_prompt(self) -> str:
        """Get system prompt for planning phase"""
        return """You are an expert coding assistant. Analyze the given task and repository context to create a detailed execution plan.
        
Respond with a JSON object containing:
        {
            "analysis": "Brief analysis of what needs to be done",
            "steps": [
                {
                    "type": "modify_file|create_file|run_tests|run_command",
                    "description": "What this step does",
                    "file_path": "path/to/file" (if applicable),
                    "changes": "Description of changes" (if applicable),
                    "command": "command to run" (if applicable),
                    "critical": true|false
                }
            ]
        }"""
    
    def _format_planning_request(self, task: Task, repo_context: Dict[str, Any], issue_context: Optional[Dict[str, Any]]) -> str:
        """Format the planning request for AI"""
        
        request = f"""Task: {task.title}
Description: {task.description}

Repository: {task.repository.full_name}
Base Branch: {task.base_branch}

Repository Context:
"""
        
        if repo_context.get('files'):
            request += f"Files ({len(repo_context['files'])}): {', '.join(repo_context['files'][:20])}"
            if len(repo_context['files']) > 20:
                request += "..."
        
        if issue_context:
            request += f"\n\nIssue Context:\nTitle: {issue_context.get('title')}\nDescription: {issue_context.get('body')}"
        
        return request
    
    def _parse_ai_plan(self, content: str) -> Dict[str, Any]:
        """Parse AI response into plan"""
        
        import json
        
        try:
            # Try to extract JSON from the response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse AI plan: {e}")
        
        # Fallback: create simple plan
        return {
            "analysis": "AI parsing failed, using fallback plan",
            "steps": [
                {
                    "type": "modify_file",
                    "description": "Manual intervention required",
                    "critical": True
                }
            ]
        }
    
    def _generate_commit_message(self, task: Task, results: Dict[str, Any]) -> str:
        """Generate commit message"""
        
        files_count = len(results.get('files_modified', []))
        
        if task.issue_number:
            return f"{task.title} (fixes #{task.issue_number})\n\nModified {files_count} files\n\nGenerated by AutoCodit Agent"
        else:
            return f"{task.title}\n\nModified {files_count} files\n\nGenerated by AutoCodit Agent"
    
    def _generate_pr_description(self, task: Task, results: Dict[str, Any]) -> str:
        """Generate PR description"""
        
        description = f"## AutoCodit Agent Task\n\n**Task:** {task.title}\n"
        
        if task.description:
            description += f"**Description:** {task.description}\n\n"
        
        if task.issue_number:
            description += f"**Closes:** #{task.issue_number}\n\n"
        
        description += "## Changes\n\n"
        
        for file_path in results.get('files_modified', []):
            description += f"- Modified `{file_path}`\n"
        
        description += "\n---\n*This PR was created automatically by AutoCodit Agent*"
        
        return description
    
    # Placeholder methods for step execution
    async def _modify_file(self, task: Task, step: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation would use GitHub API or MCP tools
        return {'files_modified': [step.get('file_path')]}
    
    async def _create_file(self, task: Task, step: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation would use GitHub API or MCP tools
        return {'files_modified': [step.get('file_path')]}
    
    async def _run_tests(self, task: Task, step: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation would use MCP tools to run tests
        return {'success': True, 'output': 'All tests passed'}
    
    async def _run_command(self, task: Task, step: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation would use MCP tools to run commands
        return {'success': True, 'output': 'Command executed successfully'}
    
    async def _run_validation_tests(self, task: Task) -> Dict[str, Any]:
        # Implementation would run validation tests
        return {'success': True, 'tests_passed': 0, 'tests_failed': 0}
    
    async def _validate_syntax(self, files: List[str]) -> Dict[str, Any]:
        # Implementation would validate file syntax
        return {'success': True, 'files_validated': len(files)}


# Celery task
@celery_app.task(bind=True, name='execute_coding_task')
def execute_coding_task(self, task_id: str):
    """Celery task for executing coding tasks"""
    
    executor = AgentExecutor()
    
    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(executor.execute_task(task_id))
        return result
    finally:
        loop.close()