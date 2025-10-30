#!/usr/bin/env python3

"""
AutoCodit Agent - Playwright MCP Server

Model Context Protocol server for browser automation,
UI testing, and screenshot capture.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import argparse
from aiohttp import web, ClientSession
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Configuration
CONFIG = {
    "port": int(os.environ.get("MCP_PORT", "2302")),
    "headless": os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
    "session_id": os.environ.get("SESSION_ID", ""),
    "task_id": os.environ.get("TASK_ID", ""),
    "workspace": "/workspace/repository",
    "screenshots_dir": "/workspace/artifacts/screenshots"
}

# Ensure screenshots directory exists
os.makedirs(CONFIG["screenshots_dir"], exist_ok=True)


def log(level: str, message: str, **kwargs):
    """Structured logging"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        "component": "playwright-mcp-server",
        "session_id": CONFIG["session_id"],
        "task_id": CONFIG["task_id"],
        **kwargs
    }
    
    print(json.dumps(log_entry), flush=True)


class PlaywrightMCPServer:
    """Playwright MCP Server implementation"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: Dict[str, Page] = {}
    
    async def initialize(self):
        """Initialize Playwright browser"""
        log("INFO", "Initializing Playwright browser")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=CONFIG["headless"]
        )
        
        # Create context
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="AutoCodit Agent/1.0.0 (+https://github.com/arturwyroslak/autocodit-agent)"
        )
        
        log("INFO", "Playwright browser initialized")
    
    async def cleanup(self):
        """Cleanup Playwright resources"""
        log("INFO", "Cleaning up Playwright resources")
        
        # Close all pages
        for page in self.pages.values():
            try:
                await page.close()
            except:
                pass
        
        # Close context and browser
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        log("INFO", "Playwright cleanup completed")
    
    async def screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot of URL"""
        url = params["url"]
        page_id = params.get("page_id", "default")
        full_page = params.get("full_page", True)
        
        try:
            # Get or create page
            if page_id not in self.pages:
                self.pages[page_id] = await self.context.new_page()
            
            page = self.pages[page_id]
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle")
            
            # Take screenshot
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{page_id}_{timestamp}.png"
            filepath = os.path.join(CONFIG["screenshots_dir"], filename)
            
            await page.screenshot(
                path=filepath,
                full_page=full_page
            )
            
            log("INFO", f"Screenshot captured: {url}", filename=filename)
            
            return {
                "url": url,
                "filename": filename,
                "filepath": filepath,
                "full_page": full_page,
                "success": True
            }
        
        except Exception as error:
            log("ERROR", f"Screenshot failed: {str(error)}", url=url)
            raise error
    
    async def validate_ui(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UI elements and behavior"""
        url = params["url"]
        validations = params.get("validations", [])
        page_id = params.get("page_id", "validation")
        
        try:
            # Get or create page
            if page_id not in self.pages:
                self.pages[page_id] = await self.context.new_page()
            
            page = self.pages[page_id]
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle")
            
            results = []
            
            for validation in validations:
                result = await self._execute_validation(page, validation)
                results.append(result)
            
            success = all(r["success"] for r in results)
            
            log("INFO", f"UI validation completed: {url}", 
               validations_count=len(validations),
               success=success)
            
            return {
                "url": url,
                "validations": results,
                "success": success
            }
        
        except Exception as error:
            log("ERROR", f"UI validation failed: {str(error)}", url=url)
            raise error
    
    async def _execute_validation(self, page: Page, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single validation"""
        validation_type = validation["type"]
        
        try:
            if validation_type == "element_exists":
                selector = validation["selector"]
                element = await page.query_selector(selector)
                success = element is not None
                
                return {
                    "type": validation_type,
                    "selector": selector,
                    "success": success,
                    "message": f"Element {'found' if success else 'not found'}: {selector}"
                }
            
            elif validation_type == "text_contains":
                selector = validation["selector"]
                expected_text = validation["text"]
                
                element = await page.query_selector(selector)
                if element:
                    actual_text = await element.text_content()
                    success = expected_text in (actual_text or "")
                    
                    return {
                        "type": validation_type,
                        "selector": selector,
                        "expected_text": expected_text,
                        "actual_text": actual_text,
                        "success": success,
                        "message": f"Text {'contains' if success else 'does not contain'} expected value"
                    }
                else:
                    return {
                        "type": validation_type,
                        "selector": selector,
                        "success": False,
                        "message": f"Element not found: {selector}"
                    }
            
            else:
                return {
                    "type": validation_type,
                    "success": False,
                    "message": f"Unknown validation type: {validation_type}"
                }
        
        except Exception as error:
            return {
                "type": validation_type,
                "success": False,
                "error": str(error),
                "message": f"Validation failed: {str(error)}"
            }


# Global server instance
playwright_server = PlaywrightMCPServer()


# HTTP handlers
async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "server": "playwright-mcp",
        "browser_connected": playwright_server.browser is not None
    })


async def tools_handler(request):
    """List available tools"""
    return web.json_response({
        "tools": [
            {
                "name": "screenshot",
                "description": "Capture screenshot of web page",
                "parameters": ["url", "page_id", "full_page"]
            },
            {
                "name": "validate_ui",
                "description": "Validate UI elements and behavior",
                "parameters": ["url", "validations", "page_id"]
            }
        ]
    })


async def tool_handler(request):
    """Execute tool"""
    tool_name = request.match_info['tool']
    
    # Parse request body
    try:
        if request.content_type == 'application/json':
            params = await request.json()
        else:
            params = {}
    except Exception:
        params = {}
    
    # Execute tool
    try:
        if hasattr(playwright_server, tool_name):
            method = getattr(playwright_server, tool_name)
            result = await method(params)
            return web.json_response(result)
        else:
            return web.json_response(
                {"error": f"Tool not found: {tool_name}"},
                status=404
            )
    
    except Exception as error:
        log("ERROR", f"Tool execution failed: {str(error)}", tool=tool_name)
        return web.json_response(
            {"error": str(error)},
            status=500
        )


# Application setup
app = web.Application()
app.router.add_get('/health', health_handler)
app.router.add_get('/tools', tools_handler)
app.router.add_post('/tools/{tool}', tool_handler)


# Startup and shutdown
async def init_app():
    """Initialize the application"""
    await playwright_server.initialize()
    return app


async def cleanup_app(app):
    """Cleanup the application"""
    await playwright_server.cleanup()


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=CONFIG["port"])
    args = parser.parse_args()
    
    # Update port from command line
    CONFIG["port"] = args.port
    
    log("INFO", f"Starting Playwright MCP Server on port {CONFIG['port']}")
    
    # Setup event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initialize and run
        app = loop.run_until_complete(init_app())
        
        web.run_app(
            app,
            host="0.0.0.0",
            port=CONFIG["port"],
            access_log=None  # Disable aiohttp access logs
        )
    
    except KeyboardInterrupt:
        log("INFO", "Shutting down Playwright MCP Server")
    finally:
        loop.run_until_complete(cleanup_app(app))
        loop.close()