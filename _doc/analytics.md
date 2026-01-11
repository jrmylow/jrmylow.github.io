# Web Analytics for Personal Sites

Summary of recommended reading on privacy-respecting analytics for personal websites.

## Core Philosophy

### Martin Tournoij (GoatCounter creator)

**"Launching GoatCounter"** (https://www.arp242.net/goatcounter.html)
- Built GoatCounter for his own personal site before commercializing
- Motivation: no good lightweight analytics existed; GA is overkill for most sites
- Believes open source is the right way to make software
- Goal: make privacy-respecting analytics freely available for smaller sites

**"Analytics on personal websites"** (https://www.arp242.net/personal-analytics.html)
- Dismisses the "vanity statistics" or "spyware" criticism of basic analytics
- Practical use case: stopped maintaining a Vim ChangeLog after analytics showed nobody read it
- Analytics help answer "is anyone reading this?" and "what resonates?"
- Compares to Stack Overflow's "people reached" metric - knowing your work helps others is motivating, not vanity

**"Why GoatCounter ignores Do Not Track"** (https://www.arp242.net/dnt.html)
- Distinguishes between tracking (following users across sites, building profiles) and counting (how many people entered through which door)
- DNT is theatre - lets trackers pretend to act ethically while knowing most users won't enable it
- GoatCounter doesn't track; it counts. DNT is irrelevant to what it does.
- If something is widely considered unethical, it shouldn't require opt-out

## Case Studies

### Gwern Branwen

**Gwern.net Website Traffic** (https://gwern.net/traffic)
- Publishes semi-annual traffic reports since 2011 with full transparency
- Tracks: page views, unique visitors, top pages, referrers
- Uses data to decide what to maintain (stopped projects nobody used)
- Publishes actual GA PDFs publicly
- Shows long-term trends: what content has lasting value vs viral spikes

### Will Larson

**"Trying Plausible"** (https://lethain.com/trying-plausibleio/)
- Switched from GA to Plausible after GA4 migration degraded UX
- GA4's default views less helpful, lost custom views, harder to configure
- Plausible: good onboarding, simple single-page dashboard
- Privacy-forward approach avoids future migrations as regulations tighten
- Criticism: Plausible markets itself as "not GA" rather than explaining its own value

### Olivier Audard

**"Farewell Google Analytics; Welcome GoatCounter"** (https://olivier.audard.net/articles/2023/01/08/farewell-google-analytics-welcome-goatcounter/)
- Had GA for 15 years without questioning it
- Motivation to switch: privacy concerns, not personal need for features
- GoatCounter targets his exact use case: basic stats for a personal blog
- Appreciates: open source, self-hostable, free hosted tier for reasonable use

## Technical Analysis

### Ctrl Blog

**"A technical and privacy review of Cloudflare Web Analytics"** (https://www.ctrl.blog/entry/review-cloudflare-analytics.html)
- Deep technical inspection of what analytics scripts actually send
- Cloudflare sends data twice per pageview (XHR then Beacon API)
- Collects Performance API data (detailed timing for assets)
- Script size comparison: Cloudflare 4.31KB vs GA 19.01KB
- Uses random UUID per pageview, not stored persistently

## Key Takeaways

1. **Counting ≠ Tracking**: Basic pageview counts don't require cookies, don't build profiles, don't follow users across sites

2. **Practical value**: Analytics answer "should I keep maintaining this?" and "what do readers want more of?"

3. **Minimalist approach works**: Page views, referrers, and device info cover 90% of useful insights

4. **Transparency builds trust**: Gwern publishes raw data; GoatCounter is open source

5. **GA is overkill**: Most personal sites don't need conversion funnels, audience segments, or ad integration

## What to Track (Minimalist)

- Page views per post
- Referrers (where readers come from)
- Device/screen size (is mobile important?)
- Geographic region (optional)

## What NOT to Track

- Individual user journeys
- Session duration obsessively
- "Engagement metrics" that optimize for addiction
- Anything requiring cookies or consent banners
