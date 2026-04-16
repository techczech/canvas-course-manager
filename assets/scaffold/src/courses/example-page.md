---
title: "Example Course Page"
layout: layouts/tabbed-course.njk
audience: "Open to all"
permalink: "example-page.html"
tags: ["example"]
category: "Getting Started"
tabs:
  - id: overview
    label: Overview
  - id: video
    label: Video
  - id: resources
    label: Resources
---

<div id="overview" class="tab-content active">
    <h2>Overview</h2>
    <p>Replace this with your course overview content.</p>

    <h3>What you will learn</h3>
    <ul>
        <li>First learning objective</li>
        <li>Second learning objective</li>
        <li>Third learning objective</li>
    </ul>
</div>

<div id="video" class="tab-content" hidden>
    <h2>Video Recording</h2>
    <div class="embed-shell">
        <iframe class="embed-frame recording-frame"
            src="https://your-video-url-here"
            allowfullscreen allow="autoplay; fullscreen"
            loading="lazy"
            title="Course recording"></iframe>
    </div>
    <div class="tip-box">
        <p><strong>Tip:</strong> If the embedded player does not load, open the recording in a new browser tab.</p>
    </div>
</div>

<div id="resources" class="tab-content" hidden>
    <h2>Resources</h2>
    <p>Add links and materials here.</p>
    <p><a class="resource-link" href="https://example.com" target="_blank" rel="noopener noreferrer">Example Resource</a></p>
</div>
