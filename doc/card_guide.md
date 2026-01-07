# Card Layout Configuration Guide

## Overview

The index page now uses a card-based layout for displaying blog posts. Each post appears as a card with:
- Title
- Date
- Excerpt/Summary

## How to Change Card Columns

Edit `_layouts/index.html` and find this line:

```html

```

Change the class to one of these options:

### Available Layouts

#### 1 Column (Full Width)
```html

```
- Mobile: 1 column
- Tablet: 1 column
- Desktop: 1 column

Best for: Long excerpts, detailed summaries

#### 2 Columns (Default)
```html

```
- Mobile: 1 column
- Tablet (48em+): 2 columns
- Desktop: 2 columns

Best for: Balanced layout, medium excerpts

#### 3 Columns
```html

```
- Mobile: 1 column
- Tablet (48em+): 2 columns
- Desktop (64em+): 3 columns

Best for: Many posts, shorter excerpts

#### 4 Columns
```html

```
- Mobile: 1 column
- Tablet (48em+): 2 columns
- Desktop (64em+): 3 columns
- Wide Desktop (80em+): 4 columns

Best for: Gallery view, very short excerpts

## Customizing Number of Posts Shown

In `_layouts/index.html`, find this line:

```liquid
{% assign recent_posts = site.posts | sort: 'date' | reverse | limit: 6 %}
```

Change the `limit: 6` number to show more or fewer posts:
- `limit: 3` - Show 3 posts
- `limit: 6` - Show 6 posts (default)
- `limit: 9` - Show 9 posts
- `limit: 12` - Show 12 posts

**Tip:** Choose a number that divides evenly by your column count for a neat grid:
- 2 columns: 4, 6, 8, 10, 12 posts
- 3 columns: 3, 6, 9, 12 posts
- 4 columns: 4, 8, 12 posts

## Adjusting Card Spacing

Edit `public/css/index-page.css` and find:

```css
.post-cards {
  display: grid;
  gap: 2rem;
  margin-bottom: 2rem;
}
```

Change `gap: 2rem;` to adjust spacing between cards:
- `gap: 1rem;` - Tighter spacing
- `gap: 2rem;` - Default spacing
- `gap: 3rem;` - Wider spacing

## Adjusting Card Padding

In `public/css/index-page.css`, find:

```css
.post-card {
  background-color: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  ...
}
```

Change `padding: 1.5rem;` to adjust internal card spacing:
- `padding: 1rem;` - Compact cards
- `padding: 1.5rem;` - Default
- `padding: 2rem;` - Spacious cards

## Disabling Card Hover Effect

If you don't want cards to lift on hover, remove these lines from `public/css/index-page.css`:

```css
.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

## Examples

### Example 1: Compact Grid (3 columns, 9 posts)
```html
<!-- In _layouts/index.html -->

  {% assign recent_posts = site.posts | sort: 'date' | reverse | limit: 9 %}
```

### Example 2: Gallery View (4 columns, 8 posts)
```html
<!-- In _layouts/index.html -->

  {% assign recent_posts = site.posts | sort: 'date' | reverse | limit: 8 %}
```

### Example 3: Detailed View (1 column, 3 posts)
```html
<!-- In _layouts/index.html -->

  {% assign recent_posts = site.posts | sort: 'date' | reverse | limit: 3 %}
```

## Testing Your Changes

After making changes:

1. Save the files
2. Rebuild Jekyll: `bundle exec jekyll serve`
3. View in browser at `http://localhost:4000/`
4. Test responsive behavior by resizing browser window

## Breakpoint Reference

- `48em` = 768px (tablet)
- `64em` = 1024px (desktop)
- `80em` = 1280px (wide desktop)

You can adjust these breakpoints in `public/css/index-page.css` if needed.
