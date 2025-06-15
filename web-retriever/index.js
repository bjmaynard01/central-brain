const express = require('express');
const axios = require('axios');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// GET endpoint for manual curl testing
app.get('/search', async (req, res) => {
  const query = req.query.q;
  console.log(`[web-retriever] Querying SearXNG (GET) for: "${query}"`);
  try {
    const response = await axios.get('http://localhost:8888/search', {
      params: {
        q: query,
        format: 'json',
        categories: 'general',
      },
      timeout: 10000,
    });

    const results = response.data.results.slice(0, 5).map((r) => ({
      title: r.title,
      url: r.url,
      snippet: r.content || '',
    }));

    res.json({ results });
  } catch (error) {
    console.error('[web-retriever] Error querying SearXNG:', error.message);
    res.status(500).json({ error: 'Failed to query SearXNG' });
  }
});

// POST endpoint for LibreChat tool calls
app.post('/v1/actions/web-search', async (req, res) => {
  const { query } = req.body;
  console.log(`[web-retriever] [TOOL_CALL] Querying SearXNG for: "${query}"`);
  try {
    const response = await axios.get('http://localhost:8888/search', {
      params: {
        q: query,
        format: 'json',
        categories: 'general',
      },
      timeout: 10000,
    });

    const results = response.data.results.slice(0, 5).map((r) => ({
      title: r.title,
      url: r.url,
      snippet: r.content || '',
    }));

    res.json({ results });
  } catch (error) {
    console.error('[web-retriever] Error querying SearXNG:', error.message);
    res.status(500).json({ error: 'Failed to query SearXNG' });
  }
});

// Start server and capture server instance
const server = app.listen(PORT, () => {
  console.log(`[web-retriever] Server is running on port ${PORT}`);
});

// Graceful shutdown on SIGTERM (docker stop, Ctrl+C, etc.)
process.on('SIGTERM', () => {
  console.log('[web-retriever] Received SIGTERM, shutting down gracefully...');
  server.close(() => {
    console.log('[web-retriever] Server stopped.');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('[web-retriever] Received SIGINT (Ctrl+C), shutting down gracefully...');
  server.close(() => {
    console.log('[web-retriever] Server stopped.');
    process.exit(0);
  });
});
