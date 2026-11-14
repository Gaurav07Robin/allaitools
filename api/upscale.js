/**
 * Real Neural AI Image Upscaler & Face Restorer API
 * Endpoint: POST /api/upscale
 * Powered by Real-ESRGAN_x4plus, GFPGAN, and CodeFormer
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

  // Enforce per-user rate limit & cooldown for heavy GPU neural upscaling
  const clientIp = getClientIp(req);
  const rateLimit = checkRateLimit(clientIp, 'upscale', {
    maxRequests: 3,
    windowMs: 15 * 60 * 1000, // 3 upscales per 15 min
    cooldownMs: 20 * 1000      // 20s cooldown between upscales
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

  const quotaInfo = {
    remaining: rateLimit.remaining,
    limit: rateLimit.limit,
    cooldownSeconds: rateLimit.cooldownSeconds,
    resetInSeconds: rateLimit.resetInSeconds
  };

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    const rawImage = (body.image || '').trim();
    const engine = body.engine || 'RealESRGAN_x4plus'; // 'RealESRGAN_x4plus', 'GFPGAN', 'CodeFormer'

    if (!rawImage) {
      return res.status(400).json({ error: 'Image data is required for upscaling.' });
    }

    // Clean base64 string
    const base64Data = rawImage.replace(/^data:image\/\w+;base64,/, '');
    const hordeKey = (process.env.AI_HORDE_API_KEY || '').trim() || '0000000000';

    console.log(`[AI Upscale] Submitting image to AI Horde with engine: ${engine}...`);

    let postProcessing = ['RealESRGAN_x4plus'];
    if (engine === 'GFPGAN' || engine === 'portrait') {
      postProcessing = ['GFPGAN', 'RealESRGAN_x4plus'];
    } else if (engine === 'CodeFormer') {
      postProcessing = ['CodeFormer', 'RealESRGAN_x4plus'];
    }

    let submitResp = await fetch('https://aihorde.net/api/v2/generate/async', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': hordeKey,
        'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
      },
      body: JSON.stringify({
        prompt: 'masterpiece, 8k uhd, sharp focus, high fidelity, 4k resolution',
        params: {
          sampler_name: 'k_euler',
          cfg_scale: 1,
          denoising_strength: 0.05,
          steps: 10,
          width: 512,
          height: 512,
          n: 1
        },
        source_image: base64Data,
        source_processing: 'img2img',
        post_processing: postProcessing,
        nsfw: false,
        censor_nsfw: true
      })
    });

    // If key returned 401, retry with anonymous key
    if (submitResp.status === 401 && hordeKey !== '0000000000') {
      console.warn('[AI Upscale] Key returned 401. Retrying with anonymous tier...');
      submitResp = await fetch('https://aihorde.net/api/v2/generate/async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': '0000000000',
          'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
        },
        body: JSON.stringify({
          prompt: 'masterpiece, 8k uhd, sharp focus, high fidelity, 4k resolution',
          params: {
            sampler_name: 'k_euler',
            cfg_scale: 1,
            denoising_strength: 0.05,
            steps: 10,
            width: 512,
            height: 512,
            n: 1
          },
          source_image: base64Data,
          source_processing: 'img2img',
          post_processing: postProcessing,
          nsfw: false,
          censor_nsfw: true
        })
      });
    }

    if (!submitResp.ok) {
      const errText = await submitResp.text();
      throw new Error(`AI Horde Upscale submit failed (${submitResp.status}): ${errText}`);
    }

    const { id } = await submitResp.json();
    if (!id) {
      throw new Error('AI Horde did not return an upscale job ID');
    }

    // Poll for upscale completion (up to 45 seconds: 15 attempts x 3s)
    const maxAttempts = 15;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      await new Promise(r => setTimeout(r, 3000));

      const checkResp = await fetch(`https://aihorde.net/api/v2/generate/status/${id}`, {
        headers: {
          'Client-Agent': 'allaitools:1.0:admin@allaitools.online'
        }
      });

      if (!checkResp.ok) continue;

      const statusData = await checkResp.json();
      if (statusData.faulted) {
        throw new Error('Neural upscale job faulted in cluster');
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
          return res.status(200).json({
            success: true,
            provider: 'aihorde-neural',
            engine: postProcessing.join(' + '),
            worker: gen.worker_name,
            image: rawImg,
            quota: quotaInfo
          });
        } else {
          base64Image = rawImg;
        }

        if (base64Image) {
          return res.status(200).json({
            success: true,
            provider: 'aihorde-neural',
            engine: postProcessing.join(' + '),
            worker: gen.worker_name,
            image: `data:${mimeType};base64,${base64Image}`,
            quota: quotaInfo
          });
        }
      }
    }

    throw new Error('AI Upscaling job timed out waiting for worker cluster');

  } catch (error) {
    console.error('[AI Upscale Error]:', error);
    return res.status(500).json({
      error: 'Neural AI upscaling failed',
      details: error.message
    });
  }
}
