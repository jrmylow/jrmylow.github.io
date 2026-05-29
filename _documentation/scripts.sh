# Terminal commands

## Build the site locally (draft mode)
bundle exec jekyll build --source docs --destination docs/_site --drafts
bundle exec jekyll serve --source docs --destination docs/_site --host 0.0.0.0 --port 4000

## Run tests
pytest
