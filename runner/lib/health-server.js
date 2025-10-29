/**
 * AutoCodit Agent Runner - Health Check Server
 * 
 * Simple HTTP server for container health checks
 */

const http = require('http');
const os = require('os');

const PORT = 8080;

// Health check data
let healthData = {
    status: 'healthy',
    startTime: new Date().toISOString(),
    uptime: 0,
    taskId: process.env.TASK_ID || 'unknown',
    sessionId: process.env.SESSION_ID || 'unknown',
    checks: {
        filesystem: true,
        memory: true,
        processes: true
    }
};

// Update health data periodically
setInterval(() => {
    const uptimeSeconds = process.uptime();
    const memUsage = process.memoryUsage();
    
    healthData.uptime = Math.floor(uptimeSeconds);
    healthData.memory = {
        used: Math.floor(memUsage.heapUsed / 1024 / 1024),
        total: Math.floor(memUsage.heapTotal / 1024 / 1024),
        external: Math.floor(memUsage.external / 1024 / 1024)
    };
    healthData.loadAverage = os.loadavg();
    
    // Check if we're running out of memory
    if (memUsage.heapUsed / memUsage.heapTotal > 0.9) {
        healthData.status = 'warning';
        healthData.checks.memory = false;
    }
}, 5000);

// Create HTTP server
const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }
    
    if (url.pathname === '/health') {
        // Main health check
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(healthData, null, 2));
        
    } else if (url.pathname === '/ready') {
        // Readiness check
        const ready = healthData.status === 'healthy' && healthData.uptime > 10;
        res.writeHead(ready ? 200 : 503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            ready,
            uptime: healthData.uptime,
            status: healthData.status
        }));
        
    } else if (url.pathname === '/metrics') {
        // Basic Prometheus metrics
        const metrics = `
# HELP agent_uptime_seconds Uptime in seconds
# TYPE agent_uptime_seconds counter
agent_uptime_seconds ${healthData.uptime}

# HELP agent_memory_used_bytes Memory usage in bytes
# TYPE agent_memory_used_bytes gauge
agent_memory_used_bytes ${process.memoryUsage().heapUsed}

# HELP agent_memory_total_bytes Total memory in bytes
# TYPE agent_memory_total_bytes gauge
agent_memory_total_bytes ${process.memoryUsage().heapTotal}

# HELP agent_load_average Load average
# TYPE agent_load_average gauge
agent_load_average{period="1m"} ${os.loadavg()[0]}
agent_load_average{period="5m"} ${os.loadavg()[1]}
agent_load_average{period="15m"} ${os.loadavg()[2]}
        `.trim();
        
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end(metrics);
        
    } else {
        // 404 for other paths
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not found' }));
    }
});

// Start server
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Health server listening on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Health server shutting down...');
    server.close(() => {
        console.log('Health server closed');
        process.exit(0);
    });
});