"use client";

import { useState, useEffect } from 'react';

interface HistoryItem {
  videoId: string;
  title: string;
  thumbnail: string;
  updatedAt: number;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [htmlContent, setHtmlContent] = useState('');
  const [progressMsg, setProgressMsg] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  
  // Settings profile states
  const [showSettings, setShowSettings] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [segmentCount, setSegmentCount] = useState('10-15');
  const [themeAccent, setThemeAccent] = useState('#4f98a3');

  useEffect(() => {
    fetchHistory();
    // Load local profile preferences
    const savedKey = localStorage.getItem('companion_api_key') || '';
    const savedSegCount = localStorage.getItem('companion_segment_count') || '10-15';
    const savedAccent = localStorage.getItem('companion_theme_accent') || '#4f98a3';
    setApiKey(savedKey);
    setSegmentCount(savedSegCount);
    setThemeAccent(savedAccent);
  }, []);

  const saveSettings = () => {
    localStorage.setItem('companion_api_key', apiKey);
    localStorage.setItem('companion_segment_count', segmentCount);
    localStorage.setItem('companion_theme_accent', themeAccent);
    setShowSettings(false);
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.history || []);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    await generateCompanion(url);
  };

  const generateCompanion = async (youtubeUrl: string) => {
    setLoading(true);
    setError('');
    setHtmlContent('');
    setProgressMsg('Step 1/3: Extracting transcript from YouTube...');

    const progressTimer = setTimeout(() => {
      setProgressMsg('Step 2/3: Generating conceptual segments and diagram schemas...');
    }, 4000);

    const progressTimer2 = setTimeout(() => {
      setProgressMsg('Step 3/3: Rendering SVG diagrams and compiling HTML...');
    }, 12000);

    try {
      // Pass the user custom API key and settings in the request body
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          youtubeUrl,
          apiKey: apiKey || undefined,
          segmentCount,
          themeAccent
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to generate companion page');
      }

      const html = await response.text();
      setHtmlContent(html);
      fetchHistory();
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

  const handleSelectHistoryItem = async (item: HistoryItem) => {
    setLoading(true);
    setError('');
    setHtmlContent('');
    setProgressMsg('Loading pre-computed companion guide...');

    try {
      const response = await fetch(`/api/session/${item.videoId}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to load cached session');
      }
      const html = await response.text();
      setHtmlContent(html);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Something went wrong while retrieving session');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans relative">
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4 flex justify-between items-center sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎧</span>
          <h1 className="text-lg font-bold bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            Visual Podcast Companion
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setShowSettings(true)}
            className="text-sm bg-zinc-800 hover:bg-zinc-700 px-3 py-1.5 rounded-lg border border-zinc-700 transition-colors flex items-center gap-1.5"
          >
            <span>⚙️</span> Settings
          </button>
          <div className="text-xs text-zinc-400 hidden sm:block">
            Transform podcasts into visual learning maps
          </div>
        </div>
      </header>

      {/* Slide-out Settings Profile Drawer */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-md bg-zinc-900 h-full border-l border-zinc-800 p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
            <div>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-zinc-100">Profile & Settings</h3>
                <button 
                  onClick={() => setShowSettings(false)}
                  className="text-zinc-400 hover:text-zinc-200 text-xl"
                >
                  &times;
                </button>
              </div>

              <div className="flex flex-col gap-5">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wider">
                    OpenRouter API Key
                  </label>
                  <input
                    type="password"
                    placeholder="sk-or-v1-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-sm focus:ring-1 focus:ring-teal-500 focus:outline-none placeholder-zinc-700"
                  />
                  <p className="text-xxs text-zinc-500 mt-1">
                    Leave blank to use global server-side API configurations. Saved locally to your browser.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wider">
                    Target Segment Count
                  </label>
                  <select
                    value={segmentCount}
                    onChange={(e) => setSegmentCount(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-sm focus:ring-1 focus:ring-teal-500 focus:outline-none"
                  >
                    <option value="5-10">Short (5 - 10 segments)</option>
                    <option value="10-15">Standard (10 - 15 segments)</option>
                    <option value="15-20">Detailed (15 - 20 segments)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wider">
                    Diagram Default Color
                  </label>
                  <div className="grid grid-cols-5 gap-2">
                    {[
                      { name: 'Teal', value: '#4f98a3' },
                      { name: 'Amber', value: '#d97706' },
                      { name: 'Emerald', value: '#059669' },
                      { name: 'Indigo', value: '#4f46e5' },
                      { name: 'Crimson', value: '#dc2626' }
                    ].map((col) => (
                      <button
                        key={col.value}
                        onClick={() => setThemeAccent(col.value)}
                        style={{ backgroundColor: col.value }}
                        className={`aspect-square rounded-lg border-2 transition-all ${
                          themeAccent === col.value ? 'border-white scale-105' : 'border-transparent opacity-70 hover:opacity-100'
                        }`}
                        title={col.name}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowSettings(false)}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-sm font-semibold rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={saveSettings}
                className="flex-1 py-3 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-sm font-semibold rounded-xl transition-all"
              >
                Save Profile
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col items-center justify-center p-6 max-w-[95%] mx-auto w-full">
        {!htmlContent ? (
          <div className="w-full max-w-4xl py-12 flex flex-col items-center">
            <div className="w-full max-w-2xl text-center mb-8">
              <h2 className="text-4xl font-extrabold tracking-tight mb-4 bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent sm:text-5xl">
                Learn Podcasts Visually
              </h2>
              <p className="text-zinc-400 text-lg max-w-lg mx-auto">
                Paste a YouTube URL to automatically generate conceptual segment breakdowns with inline SVG diagrams, highlights, and deep links.
              </p>
            </div>

            <form onSubmit={handleGenerate} className="w-full max-w-2xl flex flex-col gap-3 mb-12">
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
              <div className="flex flex-col items-center gap-4 mb-12">
                <div className="relative w-12 h-12">
                  <div className="w-12 h-12 rounded-full border-4 border-teal-500/20 border-t-teal-500 animate-spin"></div>
                </div>
                <p className="text-sm font-medium text-teal-400 animate-pulse">
                  {progressMsg}
                </p>
              </div>
            )}

            {error && (
              <div className="p-4 w-full max-w-2xl bg-red-950/30 border border-red-900/50 text-red-400 rounded-2xl text-sm mb-12">
                <strong>Error:</strong> {error}
              </div>
            )}

            {/* Previously Generated Guides Section */}
            {history.length > 0 && !loading && (
              <div className="w-full border-t border-zinc-800 pt-8">
                <h3 className="text-xl font-bold mb-6 text-zinc-300 flex items-center gap-2">
                  <span>📚</span> Previously Generated Guides
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                  {history.map((item) => (
                    <div
                      key={item.videoId}
                      onClick={() => handleSelectHistoryItem(item)}
                      className="group bg-zinc-900 border border-zinc-800 hover:border-teal-500/50 rounded-2xl overflow-hidden cursor-pointer transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-teal-500/5 flex flex-col"
                    >
                      <div className="aspect-video relative overflow-hidden bg-zinc-950">
                        <img
                          src={item.thumbnail}
                          alt={item.title}
                          className="object-cover w-full h-full group-hover:scale-105 transition-all duration-300"
                        />
                      </div>
                      <div className="p-4 flex-1 flex flex-col justify-between gap-3">
                        <h4 className="font-semibold text-zinc-200 line-clamp-2 group-hover:text-teal-400 transition-colors text-sm">
                          {item.title}
                        </h4>
                        <span className="text-xs text-zinc-500">
                          {new Date(item.updatedAt).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
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

