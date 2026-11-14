/**
 * Multi-Provider Image Generation API
 * Endpoint: POST /api/generate
 *
 * Provider Fallback Chain:
 * 1. Cloudflare Workers AI (Flux.1 Schnell / SDXL)
 * 2. AI Horde Distributed Cluster (Triggered when Cloudflare credits/quota ends)
 * 3. Pollinations Flux Engine (High-speed emergency fallback)
 */

import { checkRateLimit, getClientIp } from './rate-limiter.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed. Use POST.' });
  }

  // Enforce per-user rate limit & cooldown to protect free APIs
  const clientIp = getClientIp(req);
  const rateLimit = checkRateLimit(clientIp, 'generate', {
    maxRequests: 5,
    windowMs: 15 * 60 * 1000, // 5 requests per 15 min
    cooldownMs: 12 * 1000      // 12s cooldown between generations
  });

  res.setHeader('X-RateLimit-Limit', rateLimit.limit);
  res.setHeader('X-RateLimit-Remaining', rateLimit.remaining);
  res.setHeader('X-RateLimit-Reset', rateLimit.resetInSeconds);

  if (!rateLimit.allowed) {
    return res.status(429).json({
      success: false,
      error: rateLimit.error,
      reason: rateLimit.reason,
      retryAfterSeconds: rateLimit.retryAfterSeconds,
      remaining: rateLimit.remaining,
      limit: rateLimit.limit,
      resetInSeconds: rateLimit.resetInSeconds
    });
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    const prompt = (body.prompt || '').trim();
    const model = body.model || process.env.CLOUDFLARE_AI_MODEL || '@cf/black-forest-labs/flux-1-schnell';

    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required.' });
    }

    const accountId = (process.env.CLOUDFLARE_ACCOUNT_ID || '').trim();
    const apiToken = (process.env.CLOUDFLARE_API_TOKEN || '').trim();
    const hordeKey = (process.env.AI_HORDE_API_KEY || '').trim();

    const quotaInfo = {
      remaining: rateLimit.remaining,
      limit: rateLimit.limit,
      cooldownSeconds: rateLimit.cooldownSeconds,
      resetInSeconds: rateLimit.resetInSeconds
    };

    // Direct Pollinations AI request if selected by user
    if (model === 'pollinations' || model.startsWith('pollinations')) {
      return await generateWithPollinations(prompt, res, quotaInfo);
    }

    // Direct AI Horde request if selected by user
    if (model === 'aihorde') {
      try {
        const hordeResult = await generateWithAIHorde(prompt, hordeKey);
        return res.status(200).json({
          success: true,
          provider: 'aihorde',
          model: hordeResult.model || 'Stable Diffusion (AI Horde)',
          worker: hordeResult.worker,
          image: hordeResult.image,
          quota: quotaInfo
        });
      } catch (hordeErr) {
        console.error('Direct AI Horde call failed:', hordeErr.message);
        return await handleFallback(prompt, res, 'AI Horde queue busy. Using Flux fallback engine.', quotaInfo);
      }
    }

    // 1. Try Cloudflare Workers AI
    if (accountId && apiToken) {
      try {
        const cfUrl = `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run/${model}`;
        
        const cfResponse = await fetch(cfUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ prompt }),
        });

        if (cfResponse.ok) {
          const contentType = cfResponse.headers.get('content-type') || '';
          let base64Image = '';

          if (contentType.includes('json')) {
            const jsonResult = await cfResponse.json();
            if (jsonResult?.result?.image) {
              base64Image = jsonResult.result.image;
            }
          } else {
            const arrayBuffer = await cfResponse.arrayBuffer();
            base64Image = Buffer.from(arrayBuffer).toString('base64');
          }

          const mimeType = contentType.includes('png') ? 'image/png' : 'image/jpeg';

          if (base64Image) {
            return res.status(200).json({
              success: true,
              provider: 'cloudflare-workers-ai',
              model: model,
              image: `data:${mimeType};base64,${base64Image}`,
              quota: quotaInfo
            });
          }
        } else {
          const errorText = await cfResponse.text();
          console.warn(`Cloudflare Workers AI status ${cfResponse.status}: ${errorText}. Switching to AI Horde.`);
        }
      } catch (cfErr) {
        console.warn('Cloudflare request failed, switching to AI Horde:', cfErr.message);
      }
    }

    // 2. Fallback to AI Horde (Crowdsourced Volunteer Cluster)
    try {
      console.log('Generating via AI Horde distributed cluster...');
      const hordeResult = await generateWithAIHorde(prompt, hordeKey);
      return res.status(200).json({
        success: true,
        provider: 'aihorde',
        model: hordeResult.model || 'Stable Diffusion (AI Horde)',
        worker: hordeResult.worker,
        notice: 'Cloudflare credits/daily quota ended. Generated via AI Horde cluster.',
        image: hordeResult.image,
        quota: quotaInfo
      });
    } catch (hordeErr) {
      console.warn('AI Horde fallback failed or timed out:', hordeErr.message);
    }

    // 3. Fallback to high-speed Flux engine
    return await handleFallback(prompt, res, 'Switched to high-speed Flux engine.', quotaInfo);

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({
      error: 'Image generation failed',
      details: error.message,
    });
  }
}

/**
 * Generate image using AI Horde (https://aihorde.net/api/)
 */
async function generateWithAIHorde(prompt, customApiKey) {
  let apiKey = (customApiKey || process.env.AI_HORDE_API_KEY || '').trim() || '0000000000';

  let submitResp = await fetch('https://aihorde.net/api/v2/generate/async', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': apiKey,
      'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
    },
    body: JSON.stringify({
      prompt: prompt,
      params: {
        sampler_name: 'k_euler',
        cfg_scale: 7.5,
        steps: 20,
        height: 512,
        width: 512,
        n: 1
      },
      nsfw: false,
      censor_nsfw: true,
      models: ['stable_diffusion', 'ICBINP - I Can\'t Believe It\'s Not Photography', 'Deliberate', 'Stable Diffusion XL']
    })
  });

  // If custom API key is invalid or unregistered (401), automatically retry with anonymous key
  if (submitResp.status === 401 && apiKey !== '0000000000') {
    console.warn(`AI Horde API key (${apiKey.substring(0, 6)}...) returned 401. Retrying with public anonymous tier '0000000000'.`);
    apiKey = '0000000000';
    submitResp = await fetch('https://aihorde.net/api/v2/generate/async', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': apiKey,
        'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
      },
      body: JSON.stringify({
        prompt: prompt,
        params: {
          sampler_name: 'k_euler',
          cfg_scale: 7.5,
          steps: 20,
          height: 512,
          width: 512,
          n: 1
        },
        nsfw: false,
        censor_nsfw: true,
        models: ['stable_diffusion', 'ICBINP - I Can\'t Believe It\'s Not Photography', 'Deliberate', 'Stable Diffusion XL']
      })
    });
  }

  if (!submitResp.ok) {
    const errText = await submitResp.text();
    throw new Error(`AI Horde submit failed (${submitResp.status}): ${errText}`);
  }

  const { id } = await submitResp.json();
  if (!id) {
    throw new Error('AI Horde did not return a generation ID');
  }

  // Poll status up to 20 seconds (10 attempts x 2s)
  const maxAttempts = 10;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise(r => setTimeout(r, 2000));

    const checkResp = await fetch(`https://aihorde.net/api/v2/generate/status/${id}`, {
      headers: {
        'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
      }
    });

    if (!checkResp.ok) continue;

    const statusData = await checkResp.json();
    if (statusData.faulted) {
      throw new Error('AI Horde job faulted');
    }

    if (statusData.done && statusData.generations && statusData.generations.length > 0) {
      const gen = statusData.generations[0];
      const rawImg = gen.img;

      let base64Image = '';
      let mimeType = 'image/webp';

      if (rawImg.startsWith('http://') || rawImg.startsWith('https://')) {
        const imgFetch = await fetch(rawImg);
        if (imgFetch.ok) {
          const contentType = imgFetch.headers.get('content-type') || 'image/webp';
          mimeType = contentType.includes('png') ? 'image/png' : 'image/webp';
          const arrBuf = await imgFetch.arrayBuffer();
          base64Image = Buffer.from(arrBuf).toString('base64');
        }
      } else if (rawImg.startsWith('data:')) {
        return {
          image: rawImg,
          model: gen.model || 'Stable Diffusion (AI Horde)',
          worker: gen.worker_name
        };
      } else {
        base64Image = rawImg;
      }

      if (base64Image) {
        return {
          image: `data:${mimeType};base64,${base64Image}`,
          model: gen.model || 'Stable Diffusion (AI Horde)',
          worker: gen.worker_name
        };
      }
    }
  }

  throw new Error('AI Horde generation timed out after 20 seconds');
}

/**
 * Direct generation with Pollinations AI (Flux)
 */
async function generateWithPollinations(prompt, res, quotaInfo = null) {
  try {
    const encoded = encodeURIComponent(prompt);
    const url = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&model=flux&nologo=true`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Pollinations HTTP error ${response.status}`);
    }
    const arrayBuffer = await response.arrayBuffer();
    const base64Image = Buffer.from(arrayBuffer).toString('base64');
    return res.status(200).json({
      success: true,
      provider: 'pollinations',
      model: 'Flux (Pollinations AI)',
      image: `data:image/jpeg;base64,${base64Image}`,
      ...(quotaInfo ? { quota: quotaInfo } : {})
    });
  } catch (err) {
    return res.status(500).json({
      error: 'Pollinations AI generation failed',
      details: err.message
    });
  }
}

/**
 * Instant emergency fallback using Pollinations Flux
 */
async function handleFallback(prompt, res, notice, quotaInfo = null) {
  try {
    const encoded = encodeURIComponent(prompt);
    const fallbackUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&model=flux&nologo=true`;
    
    const response = await fetch(fallbackUrl);
    if (!response.ok) {
      throw new Error(`Fallback HTTP error ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const base64Image = Buffer.from(arrayBuffer).toString('base64');

    return res.status(200).json({
      success: true,
      provider: 'flux-fallback',
      notice: notice,
      image: `data:image/jpeg;base64,${base64Image}`,
      ...(quotaInfo ? { quota: quotaInfo } : {})
    });
  } catch (err) {
    return res.status(500).json({
      error: 'Generation failed across all available providers',
      details: err.message,
    });
  }
}
