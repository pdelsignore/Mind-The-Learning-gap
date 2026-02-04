#!/usr/bin/env python3
"""
Local development server for the D.E.E.P. Assessment tool.
Run with: python3 server.py
"""

import http.server
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

PORT = 8000
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ACCESS_CODE = os.environ.get('ACCESS_CODE', '')

# Try to load from .env file if not in environment
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('ANTHROPIC_API_KEY=') and not API_KEY:
                API_KEY = line.split('=', 1)[1].strip().strip('"').strip("'")
            elif line.startswith('ACCESS_CODE=') and not ACCESS_CODE:
                ACCESS_CODE = line.split('=', 1)[1].strip().strip('"').strip("'")

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        # Serve index-pearson.html as the default page
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index-pearson.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/analyze':
            self.handle_analyze()
        elif self.path == '/api/verify':
            self.handle_verify()
        else:
            self.send_error(404, 'Not Found')

    def handle_verify(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            submitted_code = data.get('accessCode', '')

            if not ACCESS_CODE:
                # No access code configured, allow access
                self.send_json_response({'success': True})
            elif submitted_code == ACCESS_CODE:
                self.send_json_response({'success': True})
            else:
                self.send_json_error(401, 'Invalid access code.')
        except Exception as e:
            self.send_json_error(500, f'Server error: {str(e)}')

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_analyze(self):
        if not API_KEY:
            self.send_json_error(500, 'ANTHROPIC_API_KEY not set. Create a .env file with your API key.')
            return

        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            profile_text = data.get('profileText', '')

            if len(profile_text.strip()) < 100:
                self.send_json_error(400, 'Invalid profile text. Please upload a valid LinkedIn PDF.')
                return

            # Call Claude API
            analysis = self.call_claude_api(profile_text)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(analysis).encode())

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"Claude API error: {e.code} - {error_body}")
            if e.code == 401:
                self.send_json_error(500, 'API authentication failed. Check your ANTHROPIC_API_KEY.')
            elif e.code == 429:
                self.send_json_error(429, 'Rate limit exceeded. Please wait a moment.')
            else:
                self.send_json_error(500, 'Analysis service error. Please try again.')
        except Exception as e:
            print(f"Error: {e}")
            self.send_json_error(500, f'Server error: {str(e)}')

    def call_claude_api(self, profile_text):
        prompt = f'''You are an expert in workforce development and AI-augmented learning strategies. Analyze the following LinkedIn profile and provide personalized guidance based on Pearson's D.E.E.P. Learning Framework.

The D.E.E.P. Framework consists of:

1. **DIAGNOSE**: Define task augmentation plans by understanding how AI will reshape specific roles and tasks
   - Conduct task-based analysis
   - Identify expert enthusiasts
   - Build augmentation squads
   - Identify and roll out use cases

2. **EMBED**: Instill effective learning seamlessly in the flow of work
   - Create and maintain a culture of learning
   - Embed learning in the flow of work
   - Enable social learning
   - Emphasize durable skills

3. **EVALUATE**: Measure progress toward an AI-augmented workforce
   - Build usable skills data infrastructure
   - Invest in ambient methods of skills assessment
   - Use AI to measure and personalize learning
   - Test and develop skills in authentic conditions

4. **PRIORITIZE**: Position learning as a strategic investment
   - Redefine L&D as capability curators
   - Prioritize investments around skills, not roles
   - Build a measurable skills ecosystem
   - Incentivize continuous, iterative learning

Based on this LinkedIn profile, provide:
1. A brief profile summary (name if available, current role, industry, years of experience estimate)
2. For EACH of the 4 D.E.E.P. pillars, provide:
   - 2-3 specific, actionable recommendations tailored to this person's background
   - Focus on practical steps they can take given their role and industry

LinkedIn Profile:
{profile_text}

Respond in this exact JSON format:
{{
  "profileSummary": {{
    "name": "Person's name or 'Professional'",
    "currentRole": "Their current job title",
    "industry": "Their industry",
    "experience": "Brief experience summary"
  }},
  "diagnose": {{
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  }},
  "embed": {{
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  }},
  "evaluate": {{
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  }},
  "prioritize": {{
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  }}
}}'''

        request_data = json.dumps({
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 2000,
            'messages': [{'role': 'user', 'content': prompt}]
        }).encode()

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=request_data,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': API_KEY,
                'anthropic-version': '2023-06-01'
            }
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            content = result['content'][0]['text']

            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            raise Exception('Could not parse analysis results')

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_json_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

    def log_message(self, format, *args):
        # Custom log format
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    if not API_KEY:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not found!")
        print("   Create a .env file in this directory with:")
        print("   ANTHROPIC_API_KEY=sk-ant-your-key-here\n")
    else:
        print(f"✓ API key loaded (ends with ...{API_KEY[-4:]})")

    print(f"\n🚀 Starting server at http://localhost:{PORT}")
    print(f"   Open this URL in your browser to test\n")
    print("   Press Ctrl+C to stop\n")

    server = http.server.HTTPServer(('localhost', PORT), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        server.shutdown()


if __name__ == '__main__':
    main()
