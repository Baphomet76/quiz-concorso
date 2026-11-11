const http = require('http');
const fs = require('fs');
const path = require('path');
const root = process.cwd();
const port = process.env.PORT || 8000;
const server = http.createServer((req,res)=>{
  try{
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    let filePath = path.join(root, urlPath);
    if (urlPath === '/' || urlPath === '') filePath = path.join(root,'index.html');
    fs.stat(filePath, (err, stat)=>{
      if (err) { res.statusCode=404; res.end('Not found'); return; }
      if (stat.isDirectory()) filePath = path.join(filePath,'index.html');
      const stream = fs.createReadStream(filePath);
      const ext = path.extname(filePath).toLowerCase();
      const map = {'.html':'text/html','.js':'application/javascript','.css':'text/css','.csv':'text/csv','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.woff2':'font/woff2'};
      res.setHeader('Content-Type', map[ext]||'application/octet-stream');
      stream.pipe(res);
      stream.on('error', ()=>{ res.statusCode=500; res.end('Server error'); });
    });
  }catch(e){ res.statusCode=500; res.end('Server error'); }
});
server.listen(port, '127.0.0.1', ()=>{ console.log('Server running on http://127.0.0.1:'+port); });
