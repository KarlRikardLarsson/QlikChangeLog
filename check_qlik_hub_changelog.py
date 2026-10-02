from rss_notifier import run_rss_watcher

# Qlik Cloud Hub "What's new" changelog via official RSS feed.
run_rss_watcher(
    feed_url=(
        "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/"
        "Content/Sense_Hub/Introduction/saas-change-log.htm.rss"
    ),
    state_file="last_seen_hub.txt",
    source_label="Qlik Hub",
    emoji="🆕",
)
