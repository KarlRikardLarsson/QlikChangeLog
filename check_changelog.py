from rss_notifier import run_rss_watcher

# Qlik Developer portal changelog (already RSS-based).
run_rss_watcher(
    feed_url="https://qlik.dev/rss.xml",
    state_file="last_seen.txt",
    source_label="Qlik.dev Changelog",
    emoji="🚀",
)
