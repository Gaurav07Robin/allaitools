#!/usr/bin/env python3
"""
Enrichment script for tools.json:
1. Fixes corrupt/challenge-page entries (e.g. Just a moment... -> Ask Bonbon)
2. Enriches the 54 thin-content tools with comprehensive descriptions to eliminate Soft 404s
3. Targets the top GSC search query tools (Airbrush, WayinVideo, FreeMaker, Xeve, Inkle, Casetext, ColdIQ, HIX Bypass, A2E)
   by incorporating high-CTR keywords ('photo enhancer', 'image upscaler', 'pricing', 'alternatives', etc.)
4. Fixes miscategorized tools (e.g. Inkle to Coding & Dev / Productivity)
"""

import json

with open("tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

print(f"Loaded {len(tools)} tools from tools.json.")

# Curated enhancements for thin and high-impression tools
ENRICHMENTS = {
    "just-a-moment": {
        "name": "Ask Bonbon (Bonbon AI)",
        "slug": "ask-bonbon",
        "badge": "BB",
        "description": "Ask Bonbon is an AI-powered conversational shopping assistant that helps e-commerce shoppers discover products, compare features, and get personalized recommendations through natural language.",
        "url": "https://askbonbon.com",
    },
    "sora": {
        "description": "OpenAI Sora is a revolutionary text-to-video diffusion AI model capable of generating high-definition, realistic videos up to a minute long while maintaining visual quality and adherence to complex user prompts.",
        "category_slug": "video-3d",
        "category_pill": "Video & 3D",
        "category_section": "🎥 Video & Motion FX",
    },
    "airbrush-image-enhancer": {
        "description": "Airbrush Image Enhancer is an AI photo enhancer and image upscaler that automatically increases resolution, removes noise, sharpens facial details, and unblurs photos in one click. Free alternative to manual photo editing.",
        "keywords_extra": "airbrush photo enhancer, airbrush image upscaler, photo enhancer airbrush, ai image enhancer airbrush",
    },
    "wayinvideo": {
        "description": "WayinVideo is an AI video clipping and repurposing platform that converts long-form podcasts and YouTube videos into viral short-form clips. Features smart auto-reframing, animated captions, AI B-roll, and multi-language translation.",
        "keywords_extra": "wayin free alternative, wayin pricing, wayin video generator, video clipping ai",
    },
    "freemaker-ai": {
        "description": "FreeMaker AI (Free Maker) is a versatile online AI productivity and creative workspace for generating digital assets, graphics, and templates. Discover FreeMaker pricing, reviews, and top free alternatives.",
        "keywords_extra": "freemaker.net, freemaker ai, free maker ai alternative",
    },
    "xeveai-live-ai-girlfriend-video-chat-in-your-browser": {
        "name": "Xeve.ai (Xeve AI)",
        "description": "Xeve.ai is an interactive conversational AI video chat platform providing ultra-realistic real-time avatar interactions, voice calling, and personalized virtual companion chats directly in your web browser.",
        "keywords_extra": "xeve ai, xeve.ai, xeveai, virtual companion chat",
    },
    "a2e-ai-videos": {
        "description": "A2E AI Videos is an automated AI video generator that transforms text prompts and scripts into professional videos with dynamic avatars, voiceovers, and transitions. Explore A2E pricing, APK features, and alternatives.",
        "keywords_extra": "a2e ai, a2e video generator, a2e ai apk, ae2 ai",
    },
    "inkle": {
        "name": "Inkle AI Bookkeeping",
        "description": "Inkle is an AI-native accounting and tax compliance platform built for cross-border startups and US companies. Automates transaction reconciliation, receipt categorization, Delaware franchise tax, and Form 5472 filings.",
        "category_slug": "coding-dev",
        "category_pill": "Coding & Dev",
        "category_section": "💻 Software Development & Ops",
    },
    "casetext-cocounsel": {
        "description": "Casetext CoCounsel is an enterprise AI legal assistant powered by GPT-4 and Thomson Reuters. Automates legal research, document review, deposition preparation, contract analysis, and search for law firms.",
        "category_slug": "chat-reasoning",
        "category_pill": "Chat & Reasoning",
        "category_section": "🧠 Frontier LLMs & Chat",
    },
    "coldiq": {
        "description": "ColdIQ is an AI outbound sales and lead generation system that enriches B2B prospect data, writes personalized cold email sequences, and automates high-deliverability email outreach for sales teams.",
        "category_slug": "coding-dev",
        "category_pill": "Coding & Dev",
        "category_section": "💻 Software Development & Ops",
    },
    "hix-bypass": {
        "description": "HIX Bypass is an undetectable AI humanizer designed to bypass turnitin, Originality.ai, GPTZero, and CopyLeaks by rewriting AI text into natural, human-like prose without altering the core meaning.",
        "category_slug": "chat-reasoning",
        "category_pill": "Chat & Reasoning",
        "category_section": "🧠 Frontier LLMs & Chat",
    },
    "hebbia": {
        "description": "Hebbia is an AI knowledge platform and semantic search engine designed for finance, private equity, and law. Indexes internal files and financial databases to answer complex qualitative and quantitative queries.",
    },
    "make": {
        "name": "Make (Integromat)",
        "description": "Make is a visual no-code automation platform that connects thousands of apps, APIs, and AI models to automate end-to-end business workflows without writing complex code.",
    },
    "fliki-ai": {
        "description": "Fliki AI turns text, blog posts, and scripts into engaging videos with realistic AI voiceovers in over 80 languages, stock media library integration, and auto-generated captions.",
    },
    "aragon": {
        "name": "Aragon AI Headshots",
        "description": "Aragon AI generates studio-quality professional headshots from ordinary casual selfies in minutes, ideal for LinkedIn profiles, resumes, and executive branding.",
    },
    "typefully": {
        "description": "Typefully is an AI-assisted writing, scheduling, and analytics platform designed for Twitter (X) and LinkedIn creators to craft engaging threads and grow their audience.",
    },
    "tubebuddy": {
        "description": "TubeBuddy is a YouTube SEO and channel growth toolkit with AI title generators, thumbnail analyzers, tag suggestions, and A/B testing to help video creators rank higher.",
    },
    "vecteezy-ai": {
        "description": "Vecteezy AI is a suite of generative image tools including an AI image generator, background remover, and vector generator tailored for creative professionals and designers.",
    },
    "cheatlayer": {
        "description": "Cheatlayer uses custom trained GPT agents and computer vision to automate complex web workflows, scraping, and software tasks that lack public APIs.",
    },
    "socialbee": {
        "description": "SocialBee is an AI-powered social media management tool that generates post captions, designs content schedules, and recycles evergreen posts across all major social networks.",
    },
    "outgrow": {
        "description": "Outgrow lets marketers create interactive AI calculators, quizzes, polls, assessments, and recommendation widgets that capture qualified leads and drive conversions.",
    },
    "novita-ai": {
        "description": "Novita AI provides affordable, serverless GPU infrastructure and APIs for running open-source AI models like Stable Diffusion, Flux, and Llama 3 with ultra-low latency.",
    },
    "taxley": {
        "description": "Taxley is an AI tax assistant and financial advisor that simplifies tax filing, identifies deductions, and helps freelancers and small businesses optimize tax compliance.",
    },
    "praktika": {
        "description": "Praktika is an AI English conversation coach with ultra-realistic interactive avatars that helps language learners practice speaking, improve fluency, and eliminate grammar anxiety.",
    },
    "flexclip": {
        "description": "FlexClip is an all-in-one AI video maker with auto-subtitles, AI text-to-speech, text-to-video conversion, and thousands of customizable templates for social media and business.",
    },
    "aircube": {
        "description": "AirCube is an AI workplace intelligence platform that analyzes communication, sentiment, and project velocity to optimize distributed engineering and product teams.",
    },
    "softsync": {
        "description": "SoftSync is an AI database synchronization tool that keeps disparate SaaS data sources, relational databases, and CRMs unified in real-time.",
    },
    "apollo": {
        "name": "Apollo.io AI",
        "description": "Apollo.io is a leading B2B sales intelligence and engagement platform with over 275 million contacts, AI email writing, dialer automation, and lead scoring capabilities.",
    },
    "dubtab": {
        "description": "DubTab is an AI browser extension and translation tool that provides real-time multi-language voice dubbing and subtitle translation for YouTube videos and web media.",
    },
    "talkio": {
        "name": "Talkio AI",
        "description": "Talkio AI is an interactive language tutor offering voice conversations in dozens of languages to build confidence, pronunciation accuracy, and listening skills.",
    },
    "typesafe-ai": {
        "description": "TypeSafe AI provides strict schema validation and TypeScript type enforcement for large language model outputs and JSON structured completions.",
    },
    "subscribr": {
        "description": "Subscribr is an AI scriptwriting assistant for YouTubers that models top-performing channel hooks, pacing, and storytelling frameworks to maximize viewer retention.",
    },
    "wavespeed": {
        "description": "WaveSpeed is an AI website speed optimization platform that compresses assets, optimizes critical rendering paths, and accelerates Core Web Vitals automatically.",
    },
    "10web": {
        "name": "10Web AI Website Builder",
        "description": "10Web is an automated AI website builder that recreates any website or designs new custom WordPress sites with AI-generated copy, images, and managed hosting.",
    },
    "crisp": {
        "name": "Crisp AI Chatbot",
        "description": "Crisp is an all-in-one customer messaging platform with AI chatbots that automate customer support, resolve tickets, and summarize live conversations 24/7.",
    },
    "adalo": {
        "description": "Adalo is a visual no-code app development platform that enables founders and creators to build and publish native iOS and Android apps with AI-assisted database design.",
    },
    "ankidecks": {
        "description": "AnkiDecks uses AI to transform lecture notes, PDFs, textbook chapters, and YouTube videos into spaced-repetition flashcards ready for Anki.",
    },
    "fylmai": {
        "name": "fylm.ai",
        "description": "fylm.ai is an AI-powered color grading software for filmmakers and colorists, offering neural color matching, ACES color management, and LUT generation.",
    },
    "soundverse": {
        "description": "Soundverse is an AI music and audio production platform that creates royalty-free musical tracks, instrumentals, stems, and sound effects from text prompts.",
    },
    "pixley-ai": {
        "description": "Pixley AI is an automated image enhancement and editing platform that removes unwanted backgrounds, enhances image quality, and prepares e-commerce photos.",
    },
    "jules": {
        "name": "Jules AI",
        "description": "Jules AI is an enterprise recruitment and candidate screening assistant that parses resumes, conducts initial candidate outreach, and schedules interviews.",
    },
    "riverside-audio-transcription": {
        "name": "Riverside AI Transcription",
        "description": "Riverside AI provides 99% accurate automated audio and video transcription with speaker diarization, timestamps, and multi-language translation for podcasters.",
    },
    "manus": {
        "name": "Manus AI Agent",
        "description": "Manus is an autonomous general-purpose AI agent capable of executing complex web tasks, market research, code development, and analysis across multiple applications.",
    },
    "kindredmind": {
        "description": "KindredMind uses conversational AI to capture family stories and oral histories, turning voice interviews with relatives into cherished memoirs and digital keepsakes.",
    },
    "murf": {
        "name": "Murf.ai Voice Generator",
        "description": "Murf.ai is a leading text-to-speech studio with over 120 natural-sounding AI voices in 20+ languages for e-learning, presentations, video voiceovers, and podcasts.",
    },
    "hostinger-openclaw-hosting": {
        "name": "Hostinger AI Hosting",
        "description": "Hostinger AI Hosting offers high-performance cloud server environments optimized for deploying custom AI agents, crawlers, and LLM applications.",
    },
    "lyro-by-tidio": {
        "name": "Lyro AI by Tidio",
        "description": "Lyro is a conversational AI customer service bot by Tidio that learns from your support knowledge base to resolve up to 70% of customer inquiries accurately.",
    },
    "hoppycopy": {
        "description": "HoppyCopy is an AI email marketing copywriter that generates high-converting newsletter campaigns, promotional emails, drip sequences, and abandoned cart flows.",
    },
    "hubspot-ai": {
        "name": "HubSpot AI",
        "description": "HubSpot AI embeds predictive intelligence and generative copy across marketing, sales, and service hubs to draft emails, generate blogs, and forecast revenue.",
    },
    "voluum": {
        "description": "Voluum is an enterprise performance marketing and ad tracking platform with AI traffic distribution to maximize affiliate ROI and optimize media buying.",
    },
    "wondershare-virbo": {
        "name": "Wondershare Virbo",
        "description": "Wondershare Virbo is an AI video generator with over 300 realistic multicultural avatars, royalty-free music, and text-to-speech voices for marketing and training videos.",
    },
    "moonbeam": {
        "name": "Moonbeam AI Writer",
        "description": "Moonbeam is a long-form writing assistant designed for essays, technical guides, newsletters, and books with smart outlining and style transformation tools.",
    },
    "magic-hour": {
        "name": "Magic Hour AI",
        "description": "Magic Hour is an AI video creation suite offering video-to-video style transfer, face swaps, lip sync, and text-to-video for creators and viral content.",
    },
    "nekton-ai": {
        "description": "Nekton AI lets users automate daily repetitive work by describing workflows in plain natural language, which it translates into automated multi-step scripts.",
    },
    "photoshop-generative-ai": {
        "name": "Photoshop Generative Fill",
        "description": "Adobe Photoshop Generative Fill powered by Firefly allows creators to add, extend, or remove content from images with simple text prompts non-destructively.",
    },
    "zigpoll": {
        "description": "Zigpoll is an AI customer feedback and survey platform that runs interactive on-site polls to capture zero-party data and exit-intent insights.",
    },
    "process-ai": {
        "description": "Process AI analyzes company documentation and operational logs to identify efficiency bottlenecks and automate business process management workflows.",
    },
    "artsmart-ai": {
        "name": "Artsmart AI",
        "description": "Artsmart AI is a generative visual studio that creates high-fidelity AI art, commercial stock photography, hyper-realistic portraits, and character consistency.",
    },
    "winston-ai": {
        "name": "Winston AI Detector",
        "description": "Winston AI is an industry-leading AI content detector with 99.98% accuracy for detecting text generated by ChatGPT, GPT-4, Claude, Gemini, and synthetic text.",
    },
    "botpenguin": {
        "description": "BotPenguin is an omnichannel AI chatbot builder for WhatsApp, Facebook, websites, and Telegram with live chat handoff and CRM integrations.",
    },
    "seo-gpt": {
        "description": "SEO GPT is a specialized search engine optimization AI that writes keyword-optimized meta titles, descriptions, keyword clusters, and anchor text designed to rank.",
    },
    "skybox-lab": {
        "name": "Skybox AI (Blockade Labs)",
        "description": "Skybox AI by Blockade Labs generates immersive 360-degree panoramic virtual reality skyboxes and 3D environments from text prompts in seconds.",
    },
}

updated_count = 0
for t in tools:
    slug = t.get("slug")
    if slug in ENRICHMENTS:
        for k, v in ENRICHMENTS[slug].items():
            t[k] = v
        updated_count += 1

print(f"Successfully enriched {updated_count} tools in memory.")

# Save enriched tools.json
with open("tools.json", "w", encoding="utf-8") as f:
    json.dump(tools, f, indent=2, ensure_ascii=False)

print("Saved enriched tools.json successfully.")
