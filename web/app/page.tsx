"use client";

import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [htmlContent, setHtmlContent] = useState('');
  const [progressMsg, setProgressMsg] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError('');
    setHtmlContent('');
    setProgressMsg('Step 1/3: Extracting transcript from YouTube...');

    // Simulate progress updates for a smoother visual experience
    const progressTimer = setTimeout(() => {
      setProgressMsg('Step 2/3: Generating conceptual segments and diagram schemas...');
    }, 4000);

    const progressTimer2 = setTimeout(() => {
      setProgressMsg('Step 3/3: Rendering SVG diagrams and compiling HTML...');
    }, 12000);

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtubeUrl: url }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to generate companion page');
      }

      const html = await response.text();
      setHtmlContent(html);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Something went wrong');
    } finally {
      clearTimeout(progressTimer);
      clearTimeout(progressTimer2);
      setLoading(false);
      setProgressMsg('');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans">
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4 flex justify-between items-center sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎧</span>
          <h1 className="text-lg font-bold bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            Visual Podcast Companion
          </h1>
        </div>
        <div className="text-xs text-zinc-400">
          Transform podcasts into visual learning maps
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 max-w-[95%] mx-auto w-full">
        {!htmlContent ? (
          <div className="w-full max-w-2xl py-12 flex flex-col items-center text-center">
            <h2 className="text-4xl font-extrabold tracking-tight mb-4 bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent sm:text-5xl">
              Learn Podcasts Visually
            </h2>
            <p className="text-zinc-400 text-lg mb-8 max-w-lg">
              Paste a YouTube URL to automatically generate conceptual segment breakdowns with inline SVG diagrams, highlights, and deep links.
            </p>

            <form onSubmit={handleGenerate} className="w-full flex flex-col gap-3">
              <div className="relative">
                <input
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={loading}
                  className="w-full px-5 py-4 bg-zinc-900 border border-zinc-800 rounded-2xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-50 transition-all shadow-inner"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading || !url}
                className="w-full py-4 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 font-bold rounded-2xl transition-all shadow-lg shadow-teal-500/10 active:scale-[0.99]"
              >
                {loading ? 'Processing...' : 'Generate Visual Companion'}
              </button>
            </form>

            {loading && (
              <div className="mt-8 flex flex-col items-center gap-4">
                <div className="relative w-12 h-12">
                  <div className="w-12 h-12 rounded-full border-4 border-teal-500/20 border-t-teal-500 animate-spin"></div>
                </div>
                <p className="text-sm font-medium text-teal-400 animate-pulse">
                  {progressMsg}
                </p>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 w-full bg-red-950/30 border border-red-900/50 text-red-400 rounded-2xl text-sm text-left">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        ) : (
          <div className="w-full h-[82vh] bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden flex flex-col shadow-2xl relative">
            <div className="bg-zinc-950 border-b border-zinc-800 px-4 py-2 flex justify-between items-center text-xs">
              <span className="text-zinc-500">Live Render Frame</span>
              <button
                onClick={() => setHtmlContent('')}
                className="text-zinc-400 hover:text-white bg-zinc-800 hover:bg-zinc-700 px-3 py-1 rounded-md transition-all"
              >
                ← Generate Another
              </button>
            </div>
            <iframe
              srcDoc={htmlContent}
              className="w-full flex-1 border-0"
              title="Visual Companion Output"
            />
          </div>
        )}
      </main>
    </div>
  );
}
