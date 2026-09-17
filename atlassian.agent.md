## Atlassian Agent Safety Rules

This file documents available Atlassian commands. It does **not** grant standing permission to execute them.

### Jira Write Operations Are Explicit-Opt-In Only

Unless the user explicitly asks for a Jira mutation in the current conversation, the agent must **not** perform any Jira write action.

Forbidden without explicit user instruction:
- create a Jira ticket
- edit any ticket field
- change a summary or description
- add or edit comments
- transition ticket status
- assign a ticket
- make any other Jira update

The agent must not infer permission from:
- a PR review that recommends creating a defect or follow-up task
- a workflow that mentions filing bugs or updating Jira
- the presence of the commands below in this file

If the user asks for analysis only, the agent may summarize what Jira action is recommended, but must stop short of executing any Jira mutation until the user explicitly requests it.

### Confluence Operations Are Read-Only By Default

Confluence read operations are allowed when they help answer the user's request.

Allowed without additional confirmation when relevant to the request:
- get page details
- get page by title or ID
- search pages
- list spaces or pages
- inspect comments, labels, history, restrictions, attachments, or metadata in read-only mode

Unless the user explicitly asks for a Confluence mutation in the current conversation, the agent must **not** perform any Confluence write action.

Forbidden without explicit user instruction:
- create a Confluence page
- update page title or body
- delete a page
- add or edit comments
- add labels
- upload attachments
- move or restructure pages
- make any other Confluence update

The agent must not infer permission from:
- a workflow that recommends documenting something in Confluence
- the presence of the commands below in this file
- a request to read, summarize, review, or search Confluence content

## JIRA Integration

### Get Ticket Details
Append JIRA issue key to retrieve ticket content:
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER -X GET https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>
```

### Edit Ticket Fields
Update fields on an existing ticket (replace `<ISSUE_KEY>` and modify fields as needed):
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{"fields": {"summary": "Updated summary", "description": "Updated description"}}' \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>
```

### Add Comment to Ticket
Add a comment to an existing ticket:
```bash
# Simple comment
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"body": "Your comment text here"}' \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>/comment

# Complex comment with newlines and special characters (use environment variable)
export CURL_SSL_BACKEND=secure-transport && COMMENT_BODY="Line 1\\n\\nLine 2 with \\\"quotes\\\"" && \
curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"body\":\"$COMMENT_BODY\"}" \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>/comment
```

### Create New Ticket
Create a new ticket in a project (replace `<PROJECT_KEY>` and customize fields):
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": {"key": "<PROJECT_KEY>"},
      "summary": "Ticket summary here",
      "description": "Ticket description here",
      "issuetype": {"name": "Task"}
    }
  }' \
  https://track-api.akamai.com/jira/rest/api/2/issue
```

### Transition Ticket (Change Status)
Move a ticket to a different status (get available transitions first):
```bash
# Get available transitions
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X GET \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>/transitions

# Apply a transition (replace <TRANSITION_ID>)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<TRANSITION_ID>"}}' \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>/transitions
```

### Assign Ticket
Assign a ticket to a user:
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{"name": "<USERNAME>"}' \
  https://track-api.akamai.com/jira/rest/api/2/issue/<ISSUE_KEY>/assignee
```

==================================

[//]: # (## Bitbucket Integration)

[//]: # ()
[//]: # (Base URL: `https://api.git.source.akamai.com/rest/api/latest`)

[//]: # ()
[//]: # (### Get Open PRs Where I'm a Reviewer &#40;Inbox&#41;)

[//]: # (Retrieve all pull requests where you're added as a reviewer:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/inbox/pull-requests | jq '{pullRequests: [.values[] | {)

[//]: # (  pullRequestId: .id,)

[//]: # (  title: .title,)

[//]: # (  author: .author.user.displayName,)

[//]: # (  state: .state,)

[//]: # (  cloneUrl: .fromRef.repository.links.clone[] | select&#40;.name=="ssh"&#41; | .href,)

[//]: # (  fromRefLatestCommit: .fromRef.latestCommit,)

[//]: # (  fromRefId: .fromRef.id,)

[//]: # (  toRefLatestCommit: .toRef.latestCommit,)

[//]: # (  projectKey: .fromRef.repository.project.key,)

[//]: # (  repositorySlug: .fromRef.repository.slug)

[//]: # (}]}')

[//]: # (```)

[//]: # ()
[//]: # (### Get PR Details)

[//]: # (Retrieve details of a specific pull request:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>)

[//]: # (```)

[//]: # ()
[//]: # (### Get PR Diff/Changes)

[//]: # (Retrieve the diff of a pull request:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/diff)

[//]: # (```)

[//]: # ()
[//]: # (### Get PR Activities &#40;Comments, Reviews, etc.&#41;)

[//]: # (Retrieve all activities on a pull request &#40;comments, approvals, etc.&#41;:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  "https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/activities?limit=500")

[//]: # (```)

[//]: # ()
[//]: # (### Get All Comments on a PR)

[//]: # (Filter activities to show only comments:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  "https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/activities?limit=500" | jq '[.values[] | select&#40;.action=="COMMENTED"&#41;]')

[//]: # (```)

[//]: # ()
[//]: # (### Add a General Comment to PR)

[//]: # (Add a general comment &#40;not attached to a specific line&#41;:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X POST \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"text": "Your comment text here"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments)

[//]: # (```)

[//]: # ()
[//]: # (### Add a Line Comment to PR)

[//]: # (Add a comment anchored to a specific line in the diff:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X POST \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{)

[//]: # (    "text": "Your line comment here",)

[//]: # (    "anchor": {)

[//]: # (      "line": <LINE_NUMBER>,)

[//]: # (      "lineType": "<ADDED|REMOVED|CONTEXT>",)

[//]: # (      "fileType": "TO",)

[//]: # (      "path": "path/to/file",)

[//]: # (      "srcPath": "path/to/file")

[//]: # (    })

[//]: # (  }' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments)

[//]: # (```)

[//]: # ()
[//]: # (**Anchor Field Explanations:**)

[//]: # (- `line`: Line number where the comment should appear)

[//]: # (- `lineType`: `ADDED` &#40;new line&#41;, `REMOVED` &#40;deleted line&#41;, or `CONTEXT` &#40;unchanged line near diff&#41;)

[//]: # (- `fileType`: Usually `TO` &#40;target file after changes&#41;)

[//]: # (- `path`: File path after changes &#40;after move/copy&#41;)

[//]: # (- `srcPath`: File path before changes &#40;same as `path` if file wasn't moved&#41;)

[//]: # ()
[//]: # (### Add a File-Level Comment)

[//]: # (Add a comment about a file without referencing a specific line:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X POST \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{)

[//]: # (    "text": "Your file comment here",)

[//]: # (    "anchor": {)

[//]: # (      "path": "path/to/file",)

[//]: # (      "srcPath": "path/to/file")

[//]: # (    })

[//]: # (  }' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments)

[//]: # (```)

[//]: # ()
[//]: # (### Reply to an Existing Comment)

[//]: # (Reply to an existing comment thread &#40;requires parent comment ID&#41;:)

[//]: # (```bash)

[//]: # (# First, get the comment ID from activities)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  "https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/activities?limit=500" | jq '[.values[] | select&#40;.action=="COMMENTED"&#41; | {id: .comment.id, text: .comment.text, author: .comment.author.displayName}]')

[//]: # ()
[//]: # (# Then reply to a specific comment &#40;replace <PARENT_COMMENT_ID>&#41;)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X POST \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{)

[//]: # (    "text": "Your reply text here",)

[//]: # (    "parent": {"id": <PARENT_COMMENT_ID>})

[//]: # (  }' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments)

[//]: # (```)

[//]: # ()
[//]: # (### Update/Edit a Comment)

[//]: # (Edit an existing comment &#40;requires comment ID and version&#41;:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"text": "Updated comment text", "version": <COMMENT_VERSION>}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments/<COMMENT_ID>)

[//]: # (```)

[//]: # ()
[//]: # (### Delete a Comment)

[//]: # (Delete a comment &#40;requires comment ID and version&#41;:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X DELETE \)

[//]: # (  "https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments/<COMMENT_ID>?version=<COMMENT_VERSION>")

[//]: # (```)

[//]: # ()
[//]: # (### Approve a PR)

[//]: # (Add your approval to a pull request:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"status": "APPROVED"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/participants/$USER)

[//]: # (```)

[//]: # ()
[//]: # (### Request Changes on a PR)

[//]: # (Mark the PR as needing work:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"status": "NEEDS_WORK"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/participants/$USER)

[//]: # (```)

[//]: # ()
[//]: # (### Remove Review Status &#40;Unapprove&#41;)

[//]: # (Reset your review status:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"status": "UNAPPROVED"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/participants/$USER)

[//]: # (```)

[//]: # ()
[//]: # (### Get Changed Files in a PR)

[//]: # (List all files changed in a pull request:)

[//]: # (```bash)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/changes | jq '[.values[] | {path: .path.toString, type: .type}]')

[//]: # (```)

[//]: # ()
[//]: # (### Resolve/Unresolve a Comment Task)

[//]: # (Mark a comment as resolved or reopen it:)

[//]: # (```bash)

[//]: # (# Resolve a task &#40;mark as done&#41;)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"state": "RESOLVED"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments/<COMMENT_ID>/tasks/<TASK_ID>)

[//]: # ()
[//]: # (# Reopen a resolved task)

[//]: # (export CURL_SSL_BACKEND=secure-transport && curl -E $USER \)

[//]: # (  -X PUT \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{"state": "OPEN"}' \)

[//]: # (  https://api.git.source.akamai.com/rest/api/latest/projects/<PROJECT_KEY>/repos/<REPO_SLUG>/pull-requests/<PR_ID>/comments/<COMMENT_ID>/tasks/<TASK_ID>)

[//]: # (```)

[//]: # ()
[//]: # (==================================)

## Confluence Integration

Base URL: `https://api.collaborate.akamai.com/confluence/rest/api`

### Get All Pages from a Space
Retrieve all pages from a Confluence space with pagination:
```bash
# Basic request (first 25 pages)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content?spaceKey=<SPACE_KEY>&limit=25&start=0&expand=version,space&type=page"

# With custom pagination (e.g., get 50 pages starting from position 25)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content?spaceKey=<SPACE_KEY>&limit=50&start=25&expand=version,space&type=page"

# Parse and display page titles with jq
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content?spaceKey=<SPACE_KEY>&limit=25&type=page" | jq '.results[] | {id: .id, title: .title, type: .type}'
```

**Pagination Parameters:**
- `limit`: Number of results per page (default: 25, max: varies by instance)
- `start`: Starting index for pagination (0-based)
- `expand`: Additional data to include (e.g., `version`, `space`, `body.storage`, `metadata`)

### Get Page by ID
Retrieve a specific page by its ID with full content:
```bash
# Basic page information
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>"

# With full content (storage format HTML)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>?expand=body.storage,version,space"

# With multiple expansions for complete page data
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>?expand=body.storage,version,space,metadata.labels,children.page"
```

### Get Page by Title
Search for a page by its title within a specific space:
```bash
# Find page by exact title
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content?spaceKey=<SPACE_KEY>&title=<PAGE_TITLE>&expand=body.storage,version,space&type=page"

# Example: Find page titled "Getting Started" in space "DOCS"
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content?spaceKey=DOCS&title=Getting%20Started&expand=body.storage&type=page" | jq '.results[0]'
```

**Note:** URL-encode spaces and special characters in titles (e.g., space becomes `%20`)

### Get Space Information
Retrieve information about a Confluence space:
```bash
# Get space details
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/space/<SPACE_KEY>"

# Get space with additional details
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/space/<SPACE_KEY>?expand=description.plain,homepage"

# List all spaces
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/space?limit=100"
```

### Search Pages (CQL)
Search for pages using Confluence Query Language (CQL):
```bash
# Search all pages containing specific text
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/search?cql=type=page%20and%20text~\"search%20term\""

# Search pages in a specific space
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/search?cql=type=page%20and%20space=<SPACE_KEY>&expand=body.storage"

# Search with labels
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/search?cql=type=page%20and%20label=\"tag-name\"%20and%20space=<SPACE_KEY>"
```

**Common CQL Examples:**
- `type=page and space=DOCS` - All pages in DOCS space
- `type=page and text~"keyword"` - Pages containing keyword
- `type=page and creator=username` - Pages created by specific user
- `type=page and lastmodified >= "2024-01-01"` - Recently modified pages

### Create a New Page
Create a new page in a space:
```bash
# Create a basic page
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "type": "page",
    "title": "New Page Title",
    "space": {"key": "<SPACE_KEY>"},
    "body": {
      "storage": {
        "value": "<p>This is the page content in HTML format.</p>",
        "representation": "storage"
      }
    }
  }' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content"

# Create a page as a child of another page
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "type": "page",
    "title": "Child Page Title",
    "space": {"key": "<SPACE_KEY>"},
    "ancestors": [{"id": "<PARENT_PAGE_ID>"}],
    "body": {
      "storage": {
        "value": "<p>Child page content.</p>",
        "representation": "storage"
      }
    }
  }' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content"
```

### Update an Existing Page
Update page content (requires version number):
```bash
# First, get the current version
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>?expand=version" | jq '.version.number'

# Update the page (increment version number)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X PUT \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "id": "<PAGE_ID>",
    "type": "page",
    "title": "Updated Page Title",
    "space": {"key": "<SPACE_KEY>"},
    "version": {"number": <CURRENT_VERSION + 1>},
    "body": {
      "storage": {
        "value": "<p>Updated page content.</p>",
        "representation": "storage"
      }
    }
  }' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>"
```

**Important:** Always increment the version number by 1 when updating a page.

### Delete a Page
Delete a page (moves to trash):
```bash
# Delete a page
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X DELETE \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>"

# Permanently delete (purge from trash)
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X DELETE \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>?status=trashed"
```

### Get Page Children
Retrieve child pages of a specific page:
```bash
# Get all child pages
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/page?expand=version"

# Get child pages with content
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/page?expand=body.storage,version" | jq '.results[] | {id: .id, title: .title}'
```

### Get Page Attachments
Retrieve attachments for a page:
```bash
# Get all attachments
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/attachment"

# Get attachments with download links
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/attachment?expand=version,metadata" | jq '.results[] | {title: .title, downloadLink: ._links.download}'
```

### Add Label to Page
Add labels/tags to a page:
```bash
# Add a single label
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '[{"prefix": "global", "name": "label-name"}]' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/label"

# Add multiple labels
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '[
    {"prefix": "global", "name": "documentation"},
    {"prefix": "global", "name": "important"}
  ]' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/label"
```

### Get Page Labels
Retrieve all labels on a page:
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/label" | jq '.results[] | .name'
```

### Get Page Comments
Retrieve comments on a page:
```bash
# Get all comments
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/comment?expand=body.storage,version"

# Parse comment content
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/child/comment?expand=body.storage" | jq '.results[] | {id: .id, author: .version.by.displayName, content: .body.storage.value}'
```

### Add Comment to Page
Add a comment to a page:
```bash
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "type": "comment",
    "container": {"id": "<PAGE_ID>", "type": "page"},
    "body": {
      "storage": {
        "value": "<p>This is a comment.</p>",
        "representation": "storage"
      }
    }
  }' \
  "https://api.collaborate.akamai.com/confluence/rest/api/content"
```

### Get Page History
Retrieve version history of a page:
```bash
# Get all versions
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/history"

# Get version history with authors
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/version?expand=content" | jq '.results[] | {version: .number, author: .by.displayName, when: .when, message: .message}'
```

### Export Page as PDF
Download a page as PDF:
```bash
# Export single page
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Accept: application/pdf" \
  -o "page.pdf" \
  "https://api.collaborate.akamai.com/confluence/spaces/<SPACE_KEY>/pages/<PAGE_ID>/export/pdf"
```

### Get Page Restrictions
Check access restrictions on a page:
```bash
# Get restrictions
export CURL_SSL_BACKEND=secure-transport && curl -E $USER \
  -H "Content-Type: application/json" \
  "https://api.collaborate.akamai.com/confluence/rest/api/content/<PAGE_ID>/restriction" | jq '.read.restrictions.user[] | .displayName'
```
