export default async function handler(req, res) {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Handle preflight request
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;

    if (!apiKey) {
        console.error('ANTHROPIC_API_KEY environment variable not set');
        return res.status(500).json({ error: 'Server configuration error' });
    }

    try {
        const { profileText } = req.body;

        if (!profileText || profileText.trim().length < 100) {
            return res.status(400).json({
                error: 'Invalid profile text. Please ensure you uploaded a valid LinkedIn profile PDF.'
            });
        }

        const prompt = `You are an expert in workforce development and AI-augmented learning strategies. Analyze the following LinkedIn profile and provide personalized guidance based on Pearson's D.E.E.P. Learning Framework.

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
${profileText}

Respond in this exact JSON format:
{
  "profileSummary": {
    "name": "Person's name or 'Professional'",
    "currentRole": "Their current job title",
    "industry": "Their industry",
    "experience": "Brief experience summary"
  },
  "diagnose": {
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  },
  "embed": {
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  },
  "evaluate": {
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  },
  "prioritize": {
    "summary": "One sentence overview for this pillar",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
  }
}`;

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: 'claude-sonnet-4-20250514',
                max_tokens: 2000,
                messages: [
                    {
                        role: 'user',
                        content: prompt
                    }
                ]
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Claude API error:', errorData);

            if (response.status === 401) {
                return res.status(500).json({ error: 'API authentication failed. Please contact support.' });
            } else if (response.status === 429) {
                return res.status(429).json({ error: 'Service is busy. Please try again in a moment.' });
            } else {
                return res.status(500).json({ error: 'Analysis service temporarily unavailable. Please try again.' });
            }
        }

        const data = await response.json();
        const content = data.content[0].text;

        // Parse JSON from response
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
            return res.status(500).json({ error: 'Could not parse analysis results. Please try again.' });
        }

        const analysis = JSON.parse(jsonMatch[0]);
        return res.status(200).json(analysis);

    } catch (error) {
        console.error('Analysis error:', error);
        return res.status(500).json({
            error: 'An error occurred during analysis. Please try again.'
        });
    }
}
