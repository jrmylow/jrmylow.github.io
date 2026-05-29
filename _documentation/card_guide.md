# Card Layout Configuration Guide

## Overview

The site uses a unified card-based layout system defined in `public/css/cards.css`. Cards can be used on the index page, related posts, and anywhere else card layouts are needed.

Each card displays:
- Title
- Date/metadata
- Excerpt/Summary

## Card Grid Classes

Edit the HTML template and use these classes on the grid container:

### Available Layouts

#### 1 Column (Full Width)
```html
<div class="card-grid card-grid-1">
```
- All screen sizes: 1 column

Best for: Long excerpts, detailed summaries

#### 2 Columns (Default for Index)
```html
<div class="card-grid card-grid-2">
```
- Mobile: 1 column
- Tablet (48em+): 2 columns

Best for: Balanced layout, medium excerpts

#### 3 Columns
```html
<div class="card-grid card-grid-3">
```
- Mobile: 1 column
- Tablet (48em+): 2 columns
- Desktop (64em+): 3 columns

Best for: Many posts, shorter excerpts

#### 4 Columns
```html
<div class="card-grid card-grid-4">
```
- Mobile: 1 column
- Tablet (48em+): 2 columns
- Desktop (64em+): 3 columns
- Wide Desktop (80em+): 4 columns

Best for: Gallery view, very short excerpts

## Card Structure

Basic card HTML structure:

```html
<a href="/post-url" class="card-link">
  <article class="card">
    <div class="card-content">
      <h3 class="card-title">Post Title</h3>
      <span class="card-meta">January 01, 2025</span>
      <div class="card-body">
        <p>Post excerpt or summary...</p>
      </div>
    </div>
  </article>
</a>
```

## Card Variants

### Highlighted Card
```html
<article class="card card-highlight">
```
Adds a colored border for featured content.

### Flat Card (No Background)
```html
<article class="card card-flat">
```
Removes background and border.

### No Hover Effect
```html
<article class="card card-no-hover">
```
Disables hover styling.

### Info/Warning/Success Cards
```html
<article class="card card-info">
<article class="card card-warning">
<article class="card card-success">
```
Adds a colored left border for callouts.

## Customizing Number of Posts

In `_layouts/index.html`, find:

```liquid
{% assign recent_posts = site.posts | sort: 'date' | reverse | limit: 6 %}
```

Change `limit: 6` to show more or fewer posts:
- `limit: 3` - Show 3 posts
- `limit: 6` - Show 6 posts (default)
- `limit: 9` - Show 9 posts

**Tip:** Choose a number divisible by your column count for a neat grid:
- 2 columns: 4, 6, 8, 10, 12 posts
- 3 columns: 3, 6, 9, 12 posts
- 4 columns: 4, 8, 12 posts

## CSS Customization

All card styles are in `public/css/cards.css`.

### Adjusting Card Spacing

```css
.card-grid {
  gap: 2rem;  /* Change to adjust spacing between cards */
}
```

### Adjusting Card Padding

```css
.card {
  padding: 1.5rem;  /* Change for internal card spacing */
}
```

### Adjusting Minimum Height

```css
.card {
  min-height: 250px;  /* Change for card height */
}
```

## Using Related Posts

Include related posts in any template:

```liquid
{% include related.html posts=site.related_posts limit=3 columns=3 %}
```

Parameters:
- `posts`: Array of posts (required)
- `limit`: Number to show (default: 3)
- `columns`: Grid columns 1-4 (default: 3)
- `title`: Section heading (default: "Related Posts")

## Breakpoint Reference

- `30em` = 480px (mobile)
- `48em` = 768px (tablet)
- `64em` = 1024px (desktop)
- `80em` = 1280px (wide desktop)

## Files

- `public/css/cards.css` - All card styles
- `_layouts/index.html` - Index page using cards
- `_includes/related.html` - Related posts include
