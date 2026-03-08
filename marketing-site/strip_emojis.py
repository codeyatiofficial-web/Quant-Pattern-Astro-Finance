import sys
import re

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "⭐✨🚀🔥📈💼🔮🏆🎯🌙💻⚡💎👑🛡️✅☀⚠✕✓♃♈♐📊👥⚙🌐🧠💬★📱📩🔒🎉📍📞✉✈📋📥🔄🗑📭✦"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

files = ["index.html", "script.js", "style.css", "tara-chat.js", "admin-leads.html", "disclaimer.html", "privacy-policy.html", "terms.html"]
for f in files:
    try:
        with open(f, 'r') as file:
            content = file.read()
        content = remove_emojis(content)
        with open(f, 'w') as file:
            file.write(content)
        print(f"Cleaned {f}")
    except Exception as e:
        print(f"Error processing {f}: {e}")
