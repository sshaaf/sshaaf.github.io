# GitHub Actions Workflows

This directory contains the repository automation workflows for build/deploy and content syndication.

## Workflows

- `hugo.yml`: Build and deploy the Hugo site.
- `devto-sync.yml`: Sync selected blog posts to dev.to.
- `social-announce.yml`: Announce selected blog posts to social channels.

## Secrets Used

- `ENV_FILE` (site deploy/build environment)
- `DEVTO_API_KEY`
- `BLUESKY_IDENTIFIER`
- `BLUESKY_APP_PASSWORD`
- `MASTODON_BASE_URL`
- `MASTODON_ACCESS_TOKEN`
- `DISCORD_WEBHOOK_URL`

## Post Front Matter Flags

- `devto: true` enables dev.to sync for a post.
- `devto: false` disables dev.to sync for a post.
- `social: false` disables social announcement for a post.
- `social_channels: [bluesky, mastodon, discord]` overrides social channels per post.
- `social_bluesky: true` enables Bluesky for this post.
- `social_mastodon: true` enables Mastodon for this post.
- `social_discord: true` enables Discord for this post.
- `social_text` and `social_tags` customize announcement content.

## Workflow Toggles

- `DEVTO_SYNC_ALL` (default: `false`): sync all candidate posts without requiring `devto: true`.
- `SOCIAL_ANNOUNCE_ALL` (default: `false`): announce all candidate posts using default channels.
- Manual dispatch supports `dry_run` on both content workflows.

