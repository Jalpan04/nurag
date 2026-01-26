const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 80;
const BACKEND_HOST = 'backend';
const BACKEND_PORT = 8000;

const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.json': 'application/json'
};

const server = http.createServer((req, clientRes) => {
    console.log(`${req.method} ${req.url}`);
    
    const parsedUrl = url.parse(req.url);

    // Proxy API requests
    if (parsedUrl.pathname.startsWith('/api/')) {
        const options = {
            hostname: BACKEND_HOST,
            port: BACKEND_PORT,
            path: req.url,
            method: req.method,
            headers: req.headers
        };

        const proxyReq = http.request(options, (proxyRes) => {
            clientRes.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(clientRes, { end: true });
        });

        proxyReq.on('error', (e) => {
            console.error(`Proxy Error: ${e.message}`);
            clientRes.writeHead(502);
            clientRes.end('Bad Gateway');
        });

        req.pipe(proxyReq, { end: true });
        return;
    }

    // Serve Static Files
    let filePath = '.' + parsedUrl.pathname;
    if (filePath === './') filePath = './index.html';

    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = MIME_TYPES[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                // Try index.html for SPA routing if needed (not needed here but good practice)
                // For now just 404
                clientRes.writeHead(404);
                clientRes.end('404 Not Found');
            } else {
                clientRes.writeHead(500);
                clientRes.end('Internal Server Error: ' + error.code);
            }
        } else {
            clientRes.writeHead(200, { 'Content-Type': contentType });
            clientRes.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
