# Blog Enhancement TODO

## High Priority Features

### 1. Index Page (`index.html` or `_pages/index.md`)
- [ ] Contains a section for the website introduction
- [ ] Contains the most recent posts and their title and summary
- [ ] Contains a selection of top posts and their title and summary
- [ ] Display post title, date, and summary/excerpt
- [ ] Add styling to match the existing Lanyon theme
- [ ] Ensure responsive design for mobile devices

### 2. Pagination
- [ ] Configure Jekyll pagination settings in `_config.yml`
  - [ ] Set posts per page to 20
  - [ ] Verify `jekyll-paginate` plugin is working
- [ ] Create pagination navigation UI
  - [ ] "Previous" and "Next" buttons/links
  - [ ] Page numbers (1, 2, 3, etc.)
  - [ ] Handle first page (no "Previous" link)
  - [ ] Handle last page (no "Next" link)
- [ ] Style pagination to match theme
  - [ ] Use existing `.pagination` and `.pagination-item` classes
  - [ ] Ensure proper spacing and alignment
- [ ] Test pagination with multiple posts
  - [ ] Create test posts if needed
  - [ ] Verify page transitions work correctly
  - [ ] Check that post counts are accurate

### 3. Tag Functionality
- [ ] Design tag taxonomy
  - [ ] Review existing posts for tag examples (e.g., "top" tag in post1)
  - [ ] Define tag naming conventions
  - [ ] Decide on tag display format
- [ ] Create tag pages/views
  - [ ] Option A: Single tag index page listing all tags
  - [ ] Option B: Individual page per tag
  - [ ] Option C: Both approaches
- [ ] Implement tag filtering
  - [ ] Display posts by tag
  - [ ] Show tag count (number of posts per tag)
  - [ ] Add "Related posts by tag" functionality
- [ ] Add tag display on posts
  - [ ] Show tags at top or bottom of post
  - [ ] Make tags clickable/linkable
  - [ ] Style tags (badges, pills, or inline text)
- [ ] Create tag navigation
  - [ ] Add tags to sidebar navigation
  - [ ] Or create dedicated "Tags" page
- [ ] Update post layout (`_layouts/post.html`)
  - [ ] Add tag display section
  - [ ] Link tags to tag archive/filter pages
- [ ] Test tag functionality
  - [ ] Add tags to multiple posts
  - [ ] Verify tag pages generate correctly
  - [ ] Check tag-based navigation

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
- [ ] Consider adding JSON Feed format
  - [ ] Create `feed.json` alongside `atom.xml`
  - [ ] Provide both RSS and JSON options
- [ ] Add feed icon/link to sidebar
  - [ ] Make feed URL easily discoverable
  - [ ] Add RSS icon from Font Awesome or similar
- [ ] Optimize feed content
  - [ ] Include full post content vs. excerpts
  - [ ] Add featured images if applicable
  - [ ] Include proper author information

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

### Configuration Updates Needed
```yaml
# _config.yml additions/changes
paginate: 10 # or desired number
paginate_path: "/page:num/"

# Tag plugin (if needed)
# Consider jekyll-tagging or manual implementation
```

### Testing Checklist
- [ ] Build site locally with `bundle exec jekyll serve`
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
