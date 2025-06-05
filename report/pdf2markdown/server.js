import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3030;

// Set up static file directory, mapped to /report path
app.use('/report', express.static(path.join(__dirname, 'dist')));

// Simple root route handler
app.get('/report', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'), (err) => {
    if (err) {
      res.status(404).send('index.html not found');
    }
  });
});

// Redirect root path to /report
app.get('/', (req, res) => {
  res.redirect('/report');
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(`Report access URL: http://localhost:${PORT}/report`);
  console.log(`Static files directory: ${path.join(__dirname, 'dist')}`);
});
