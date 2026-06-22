import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { youtubeUrl } = await request.json();

    if (!youtubeUrl) {
      return NextResponse.json({ error: 'YouTube URL is required' }, { status: 400 });
    }

    // Resolve paths relative to the root project directory
    const repoRoot = path.resolve(process.cwd(), '..');
    const mainPyPath = path.join(repoRoot, 'src', 'main.py');
    const venvPythonPath = path.join(repoRoot, 'venv', 'bin', 'python');

    console.log(`Running pipeline for URL: ${youtubeUrl}`);
    
    // Run the Python orchestrator
    // Under Linux, we use the virtual environment's python interpreter
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
    console.error('Error generating companion page:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to generate companion page' },
      { status: 500 }
    );
  }
}
