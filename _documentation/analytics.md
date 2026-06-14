# Analytics

Working notes for the site analytics, objectives, and design.

## Objectives:

The goal was to implement tracking that I wouldn't mind as a visitor. Privacy-respecting, lightweight, and avoiding tracking. I'm not interested in fingerprinting viewers, it's enough to know what's getting traction and what's not. In this site, I use [GoatCounter](https://www.goatcounter.com/) for this purpose.

## Implementation

The counter loads from `_layouts/default.html`:

```html
<script data-goatcounter="https://jrmylow-gc.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
<noscript>
  <img src="https://jrmylow-gc.goatcounter.com/count?p={{ page.url }}">
</noscript>
```

## Analysis

Upcoming, a data-driven view of the analytics, including an understanding of variation. Candidate tools are sqlite and python for the time being, but very much WIP.

## References
- GoatCounter docs: <https://www.goatcounter.com/help>
- GoatCounter privacy/GDPR: <https://www.goatcounter.com/help/gdpr>
- API (for the optional export): <https://www.goatcounter.com/help/api>
