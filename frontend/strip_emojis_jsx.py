import os
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
        "⭐✨🚀🔥📈💼🔮🏆🎯🌙💻⚡💎��🛡️✅☀⚠✕✓♃♈♐📊👥⚙🌐🧠💬★📱📩🔒🎉📍📞✉✈📋📥🔄🗑📭✦��🥈🥉🌅📉📅🔬⛓️🏦📰〽️↑↓☀️🌑🪐⭐👨‍🏫❌⚠️🔐🎟️⏳▶️🔁"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

for root, _, files in os.walk('src'):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            # replace emojis
            new_content = remove_emojis(content)
            # wait, in JSX sometimes emojis are directly in the text, so replacing them is fine.
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Cleaned {filepath}")
