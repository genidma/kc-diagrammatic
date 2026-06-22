import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function GET(
  request: Request,
  { params }: { params: Promise<{ videoId: string }> }
) {
  try {
    const { videoId } = await params;

    if (!videoId) {
      return NextResponse.json({ error: 'Video ID is required' }, { status: 400 });
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const cacheDir = path.join(repoRoot, 'data', 'cache');
    const segmentsPath = path.join(cacheDir, `${videoId}.json`);

    // Verify if cache file exists
    if (!fs.existsSync(segmentsPath)) {
      return NextResponse.json({ error: 'Session not found in cache' }, { status: 404 });
    }

    // Call Layer 3 renderer directly using python3 to generate the companion HTML
    const mainPyPath = path.join(repoRoot, 'src', 'main.py');
    const venvPythonPath = path.join(repoRoot, 'venv', 'bin', 'python');
    const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}`;

    console.log(`Reviving cached session for video ID: ${videoId}`);

    // This command executes main.py, which detects the cached segments,
    // copies them into place, and runs the Jinja2 template rendering instantly.
    await execAsync(`"${venvPythonPath}" "${mainPyPath}" "${youtubeUrl}"`);

    // Read the compiled companion HTML
    const outputPath = path.join(repoRoot, 'output', 'companion.html');
    if (!fs.existsSync(outputPath)) {
      throw new Error('Generated companion.html not found on disk');
    }

    const htmlContent = fs.readFileSync(outputPath, 'utf-8');

    return new Response(htmlContent, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
      },
    });

  } catch (error: any) {
    console.error('Error reviving session:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to revive session' },
      { status: 500 }
    );
  }
}
