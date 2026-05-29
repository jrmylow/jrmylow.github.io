# Blog Enhancement TODO

## High Priority Features

### 1. Index Page (`index.html` or `_pages/index.md`)
- [X] Contains a section for the website introduction
- [X] Contains the most recent posts and their title and summary
- [ ] Contains a selection of top posts and their title and summary
- [X] Display post title, date, and summary/excerpt
- [X] Add styling to match the existing Lanyon theme
- [ ] Ensure responsive design for mobile devices

### 2. Pagination
- [X] Set up multiple draft pages
- [ ] Set up content aggregation pages (e.g. essays) as template
- [ ] Configure Jekyll pagination settings (20 posts per page) and verify plugin is working
- [ ] Create pagination navigation (prev/next buttons, page numbers, first and last pages)
- [ ] Make theme consistent
- [ ] Test pagination

### 3. Tag Functionality
- [ ] "Top" tag for top posts
- [ ] Draft additional tags
- [ ] Set up for automatic tag-based view / filtering?
- [ ] Set up page that aggregates all tags?
- [ ] Add tag display on posts
- [ ] Test tag functionality

## Medium Priority

### 4. Index Page Enhancements
- [ ] Add search functionality (client-side with Lunr.js or similar)
- [ ] Implement "Load more" button as alternative to pagination
- [ ] Add post categories in addition to tags
- [ ] Create archive page (posts by month/year)
- [ ] Add estimated reading time to post previews

### 5. Tag System Enhancements
- [ ] Implement tag cloud visualization
- [ ] Add tag suggestions when writing posts
- [ ] Create tag management utilities
- [ ] Add tag descriptions/metadata
- [ ] Implement tag aliases or synonyms

## Low Priority

### 6. Atom/RSS Feed
- [ ] Review existing `atom.xml` file
  - [ ] Verify XML structure is valid
  - [ ] Check that all posts are included
  - [ ] Ensure proper date formatting
- [ ] Test feed in RSS readers
  - [ ] Feedly
  - [ ] RSS readers in browsers
  - [ ] Other common readers
- [ ] Add feed auto-discovery links
  - [ ] Add `<link>` tag in `<head>` section
  - [ ] Already present in `_includes/head.html` - verify it works
- [ ] Add feed icon/link to sidebar

### 7. Performance Enhancements
- [ ] Try to find a way to reduce site size
- [ ] Try to find a way to reduce site load time

## Implementation Notes

### File Structure
```
/
├── _config.yml (pagination settings, plugins)
├── _includes/
│   ├── sidebar.html (add tags link)
│   └── post-tags.html (new: tag display component)
├── _layouts/
│   ├── default.html
│   ├── post.html (update with tags)
│   └── tag-page.html (new: for tag archives)
├── _pages/
│   ├── index.md (update or create new)
│   └── tags.md (new: tag index page)
├── _posts/ (add tags to front matter)
└── atom.xml (review and test)
```

### Testing Checklist
- [ ] Build site locally with `bundle exec jekyll serve --draft`
- [ ] Check all navigation links work
- [ ] Verify pagination on multiple pages
- [ ] Click through tag links and verify filtering
- [ ] Test RSS feed in reader
- [ ] Review responsive design on mobile
- [ ] Validate HTML and CSS
- [ ] Check accessibility (proper heading hierarchy, alt text, etc.)
- [ ] Test with screen reader if possible

## Resources
- Jekyll Pagination: https://jekyllrb.com/docs/pagination/
- Jekyll Tags: https://jekyllrb.com/docs/posts/#tags-and-categories
- Atom Feed Spec: https://validator.w3.org/feed/docs/atom.html
- Jekyll Tag Archives: https://codinfox.github.io/dev/2015/03/06/use-tags-and-categories-in-your-jekyll-based-github-pages/
