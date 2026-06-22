import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const repoRoot = path.resolve(process.cwd(), '..');
    const cacheDir = path.join(repoRoot, 'data', 'cache');

    if (!fs.existsSync(cacheDir)) {
      return NextResponse.json({ history: [] });
    }

    const files = fs.readdirSync(cacheDir);
    const historyList = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(cacheDir, file);
        try {
          const stats = fs.statSync(filePath);
          const rawData = fs.readFileSync(filePath, 'utf-8');
          const data = JSON.parse(rawData);

          // We extract the title and video ID from the saved cache
          const videoId = file.replace('.json', '');
          
          let title = `Video Session (${videoId})`;
          if (data && data.segments && data.segments.length > 0) {
            title = data.segments[0].title || title;
          } else if (Array.isArray(data) && data.length > 0) {
            title = data[0].title || title;
          }

          const thumbnail = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;

          historyList.push({
            videoId,
            title,
            thumbnail,
            updatedAt: stats.mtimeMs,
          });
        } catch (e) {
          console.error(`Error parsing cache file ${file}:`, e);
        }
      }
    }

    // Sort by most recently modified first
    historyList.sort((a, b) => b.updatedAt - a.updatedAt);

    return NextResponse.json({ history: historyList });
  } catch (error: any) {
    console.error('Error fetching history:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch history list' },
      { status: 500 }
    );
  }
}
