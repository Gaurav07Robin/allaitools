import fs from 'fs';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';
import { checkRateLimit, getClientIp } from './api/rate-limiter.js';

async function runHorde(prompt, customApiKey) {
  let apiKey = (customApiKey || '').trim() || '0000000000';

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

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    server: {
      port: 3000,
      host: '0.0.0.0',
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
    plugins: [
      {
        name: 'static-html-router',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            if (req.method !== 'GET' && req.method !== 'HEAD') return next();

            const url = (req.url || '').split('?')[0];
            // Skip api or vite internals
            if (url.startsWith('/api/') || url.startsWith('/@') || url.startsWith('/node_modules/') || url.startsWith('/src/')) {
              return next();
            }

            // Let Vite serve root index.html
            if (url === '/' || url === '') {
              return next();
            }

            const publicDir = path.resolve(process.cwd(), 'public');
            const decodedPath = decodeURIComponent(url);

            let filePath = '';
            if (decodedPath.endsWith('/')) {
              const p = path.join(publicDir, decodedPath, 'index.html');
              if (fs.existsSync(p) && fs.statSync(p).isFile()) {
                filePath = p;
              }
            } else {
              const pIndex = path.join(publicDir, decodedPath, 'index.html');
              const pHtml = path.join(publicDir, `${decodedPath}.html`);
              const pDirect = path.join(publicDir, decodedPath);
              if (fs.existsSync(pIndex) && fs.statSync(pIndex).isFile()) {
                filePath = pIndex;
              } else if (fs.existsSync(pHtml) && fs.statSync(pHtml).isFile()) {
                filePath = pHtml;
              } else if (fs.existsSync(pDirect) && fs.statSync(pDirect).isFile() && pDirect.endsWith('.html')) {
                filePath = pDirect;
              }
            }

            if (filePath) {
              const content = fs.readFileSync(filePath, 'utf8');
              res.setHeader('Content-Type', 'text/html; charset=utf-8');
              res.statusCode = 200;
              return res.end(content);
            }

            next();
          });
        }
      },
      {
        name: 'cloudflare-api-middleware',
        configureServer(server) {
          server.middlewares.use('/api/generate', async (req, res) => {
            if (req.method === 'OPTIONS') {
              res.setHeader('Access-Control-Allow-Origin', '*');
              res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
              res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
              res.statusCode = 200;
              return res.end();
            }

            if (req.method !== 'POST') {
              res.statusCode = 405;
              return res.end(JSON.stringify({error: 'Method not allowed'}));
            }

            // Per-user rate limit & cooldown check
            const clientIp = getClientIp(req);
            const rateLimit = checkRateLimit(clientIp, 'generate', {
              maxRequests: 5,
              windowMs: 15 * 60 * 1000,
              cooldownMs: 12 * 1000
            });

            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('X-RateLimit-Limit', rateLimit.limit);
            res.setHeader('X-RateLimit-Remaining', rateLimit.remaining);
            res.setHeader('X-RateLimit-Reset', rateLimit.resetInSeconds);

            if (!rateLimit.allowed) {
              res.statusCode = 429;
              return res.end(JSON.stringify({
                success: false,
                error: rateLimit.error,
                reason: rateLimit.reason,
                retryAfterSeconds: rateLimit.retryAfterSeconds,
                remaining: rateLimit.remaining,
                limit: rateLimit.limit,
                resetInSeconds: rateLimit.resetInSeconds
              }));
            }

            const quotaInfo = {
              remaining: rateLimit.remaining,
              limit: rateLimit.limit,
              cooldownSeconds: rateLimit.cooldownSeconds,
              resetInSeconds: rateLimit.resetInSeconds
            };

            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', async () => {
              try {
                const data = JSON.parse(body || '{}');
                const prompt = (data.prompt || '').trim();
                const model = data.model || env.CLOUDFLARE_AI_MODEL || '@cf/black-forest-labs/flux-1-schnell';

                const accountId = (env.CLOUDFLARE_ACCOUNT_ID || '').trim();
                const apiToken = (env.CLOUDFLARE_API_TOKEN || '').trim();
                const hordeKey = (env.AI_HORDE_API_KEY || '').trim();

                // Direct Pollinations AI if selected
                if (model === 'pollinations' || model.startsWith('pollinations')) {
                  try {
                    const encoded = encodeURIComponent(prompt);
                    const pUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&model=flux&nologo=true`;
                    const pResp = await fetch(pUrl);
                    const pBuf = await pResp.arrayBuffer();
                    const b64 = Buffer.from(pBuf).toString('base64');
                    return res.end(JSON.stringify({
                      success: true,
                      provider: 'pollinations',
                      model: 'Flux (Pollinations AI)',
                      image: `data:image/jpeg;base64,${b64}`,
                      quota: quotaInfo
                    }));
                  } catch (pErr) {
                    console.error('Direct Pollinations error:', pErr.message);
                  }
                }

                // Direct AI Horde if selected
                if (model === 'aihorde') {
                  try {
                    const hordeResult = await runHorde(prompt, hordeKey);
                    return res.end(JSON.stringify({
                      success: true,
                      provider: 'aihorde',
                      model: hordeResult.model || 'Stable Diffusion (AI Horde)',
                      worker: hordeResult.worker,
                      image: hordeResult.image,
                      quota: quotaInfo
                    }));
                  } catch (hordeErr) {
                    console.error('Direct AI Horde error:', hordeErr.message);
                  }
                }

                // 1. Call Cloudflare Workers AI with the valid credentials
                if (accountId && apiToken && model !== 'aihorde') {
                  try {
                    const cfUrl = `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run/${model}`;
                    const cfResp = await fetch(cfUrl, {
                      method: 'POST',
                      headers: {
                        'Authorization': `Bearer ${apiToken}`,
                        'Content-Type': 'application/json'
                      },
                      body: JSON.stringify({ prompt })
                    });

                    if (cfResp.ok) {
                      const contentType = cfResp.headers.get('content-type') || '';
                      let base64Image = '';

                      if (contentType.includes('json')) {
                        const jsonResult = await cfResp.json();
                        if (jsonResult?.result?.image) {
                          base64Image = jsonResult.result.image;
                        }
                      } else {
                        const arrayBuf = await cfResp.arrayBuffer();
                        base64Image = Buffer.from(arrayBuf).toString('base64');
                      }

                      const mimeType = contentType.includes('png') ? 'image/png' : 'image/jpeg';

                      if (base64Image) {
                        return res.end(JSON.stringify({
                          success: true,
                          provider: 'cloudflare-workers-ai',
                          model,
                          image: `data:${mimeType};base64,${base64Image}`,
                          quota: quotaInfo
                        }));
                      }
                    } else {
                      const errText = await cfResp.text();
                      console.warn(`Cloudflare status ${cfResp.status}: ${errText}. Switching to AI Horde.`);
                    }
                  } catch (cfErr) {
                    console.warn('Cloudflare call failed, switching to AI Horde:', cfErr.message);
                  }
                }

                // 2. Fallback to AI Horde distributed cluster
                try {
                  console.log('Generating via AI Horde distributed cluster...');
                  const hordeResult = await runHorde(prompt, hordeKey);
                  return res.end(JSON.stringify({
                    success: true,
                    provider: 'aihorde',
                    model: hordeResult.model || 'Stable Diffusion (AI Horde)',
                    worker: hordeResult.worker,
                    notice: 'Cloudflare quota/credits finished. Generated with AI Horde cluster.',
                    image: hordeResult.image,
                    quota: quotaInfo
                  }));
                } catch (hordeErr) {
                  console.warn('AI Horde fallback failed:', hordeErr.message);
                }

                // 3. Fallback to free Flux engine
                const encoded = encodeURIComponent(prompt);
                const fbUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&model=flux&nologo=true`;
                const fbResp = await fetch(fbUrl);
                const fbBuf = await fbResp.arrayBuffer();
                const b64 = Buffer.from(fbBuf).toString('base64');
                return res.end(JSON.stringify({
                  success: true,
                  provider: 'flux-fallback',
                  notice: 'Using high-speed Flux fallback engine.',
                  image: `data:image/jpeg;base64,${b64}`,
                  quota: quotaInfo
                }));
              } catch (e) {
                res.statusCode = 500;
                res.end(JSON.stringify({error: e.message}));
              }
            });
          });

          // API Upscale Middleware
          server.middlewares.use('/api/upscale', async (req, res) => {
            if (req.method === 'OPTIONS') {
              res.setHeader('Access-Control-Allow-Origin', '*');
              res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
              res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
              res.statusCode = 200;
              return res.end();
            }

            if (req.method !== 'POST') {
              res.statusCode = 405;
              return res.end(JSON.stringify({error: 'Method not allowed'}));
            }

            // Per-user rate limit & cooldown for heavy neural upscaling
            const clientIp = getClientIp(req);
            const rateLimit = checkRateLimit(clientIp, 'upscale', {
              maxRequests: 3,
              windowMs: 15 * 60 * 1000,
              cooldownMs: 20 * 1000
            });

            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('X-RateLimit-Limit', rateLimit.limit);
            res.setHeader('X-RateLimit-Remaining', rateLimit.remaining);
            res.setHeader('X-RateLimit-Reset', rateLimit.resetInSeconds);

            if (!rateLimit.allowed) {
              res.statusCode = 429;
              return res.end(JSON.stringify({
                success: false,
                error: rateLimit.error,
                reason: rateLimit.reason,
                retryAfterSeconds: rateLimit.retryAfterSeconds,
                remaining: rateLimit.remaining,
                limit: rateLimit.limit,
                resetInSeconds: rateLimit.resetInSeconds
              }));
            }

            const quotaInfo = {
              remaining: rateLimit.remaining,
              limit: rateLimit.limit,
              cooldownSeconds: rateLimit.cooldownSeconds,
              resetInSeconds: rateLimit.resetInSeconds
            };

            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', async () => {
              try {
                const data = JSON.parse(body || '{}');
                const rawImage = (data.image || '').trim();
                const engine = data.engine || 'RealESRGAN_x4plus';

                if (!rawImage) {
                  res.statusCode = 400;
                  return res.end(JSON.stringify({error: 'Image is required'}));
                }

                const base64Data = rawImage.replace(/^data:image\/\w+;base64,/, '');
                const hordeKey = (env.AI_HORDE_API_KEY || '').trim() || '0000000000';

                let postProcessing = ['RealESRGAN_x4plus'];
                if (engine === 'GFPGAN' || engine === 'portrait') {
                  postProcessing = ['GFPGAN', 'RealESRGAN_x4plus'];
                } else if (engine === 'CodeFormer') {
                  postProcessing = ['CodeFormer', 'RealESRGAN_x4plus'];
                }

                res.setHeader('Content-Type', 'application/json');
                res.setHeader('Access-Control-Allow-Origin', '*');

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

                if (submitResp.status === 401 && hordeKey !== '0000000000') {
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
                if (!id) throw new Error('AI Horde did not return an upscale job ID');

                const maxAttempts = 15;
                for (let attempt = 0; attempt < maxAttempts; attempt++) {
                  await new Promise(r => setTimeout(r, 3000));
                  const checkResp = await fetch(`https://aihorde.net/api/v2/generate/status/${id}`, {
                    headers: { 'Client-Agent': 'allaitools:1.0:admin@allaitools.online' }
                  });
                  if (!checkResp.ok) continue;
                  const statusData = await checkResp.json();
                  if (statusData.faulted) throw new Error('Neural upscale job faulted in cluster');

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
                      return res.end(JSON.stringify({
                        success: true,
                        provider: 'aihorde-neural',
                        engine: postProcessing.join(' + '),
                        worker: gen.worker_name,
                        image: rawImg,
                        quota: quotaInfo
                      }));
                    } else {
                      base64Image = rawImg;
                    }

                    if (base64Image) {
                      return res.end(JSON.stringify({
                        success: true,
                        provider: 'aihorde-neural',
                        engine: postProcessing.join(' + '),
                        worker: gen.worker_name,
                        image: `data:${mimeType};base64,${base64Image}`,
                        quota: quotaInfo
                      }));
                    }
                  }
                }

                throw new Error('AI Upscaling job timed out waiting for worker cluster');
              } catch (e) {
                res.statusCode = 500;
                res.end(JSON.stringify({error: e.message}));
              }
            });
          });
        }
      }
    ]
  };
});
