---
layout: blogpost
# Basic title information
title: test_page
subtitle: sub_title
summary:
 - p: A meaningful summary of the article contents. Should cover approximately 2-3 lines.
 - p: 

# Sections if needed
sections:
 - name: Name of section 1
   link: "#id_01"
 - name: Name of section 2
   link: "#id_02"
 - name: Name of section 3
   link: "#id_03"

date: 1
author: 2

---

## Testing
Content is written in [Markdown](https://learnxinyminutes.com/docs/markdown/). Plain text format allows you to focus on your **content**.


## Template for applying html classes and custom ids in kramdown
{: #id_01}

Paragraph to apply stuff to. Lorem ipsum blah blah blah...
{: .myclass1 .myclass2 #id_02}


## Lists
The following list has the my-class css class applied to it

1. Test
2. Test
3. Test
{: .my-class }

## Template for tables

| head | head |
| :--- | ---: |
| A simple | table |
| with multiple | lines|
{: .my-class }