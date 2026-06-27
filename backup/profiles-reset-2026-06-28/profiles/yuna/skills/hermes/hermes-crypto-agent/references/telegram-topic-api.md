# Telegram Forum/Topic API Reference

## Key Endpoints

### Create Forum Topic
```
POST /createForumTopic
{
  "chat_id": "-1001234567890",
  "name": "Topic Name",
  "icon_color": 0x6FB9F0  // Optional, hex color
}
```
Returns: `{ "message_thread_id": 123 }`

### Send Message to Topic
```
POST /sendMessage
{
  "chat_id": "-1001234567890",
  "message_thread_id": 123,  // Topic ID
  "text": "Message text",
  "parse_mode": "HTML"  // or "MarkdownV2"
}
```

### Edit Forum Topic
```
POST /editForumTopic
{
  "chat_id": "-1001234567890",
  "message_thread_id": 123,
  "name": "New Name",
  "icon_custom_emoji_id": "emoji_id"
}
```

### Delete Forum Topic
```
POST /deleteForumTopic
{
  "chat_id": "-1001234567890",
  "message_thread_id": 123
}
```

## Icon Colors (Hex)
- 0x6FB9F0 — Blue (default)
- 0xFFD67E — Yellow
- 0xCB86DB — Purple
- 0xC3E88D — Green
- 0xFF9B85 — Orange
- 0x8ECCCC — Cyan

## Prerequisites
- Group must be supergroup with topics enabled
- Bot must be admin with "Manage Topics" permission
- Chat ID is negative for groups (e.g., `-1001234567890`)

## Get Chat ID
1. Forward message from group to @userinfobot
2. Or use: `GET /getUpdates` and find chat.id in response

## Topic ID
- First topic (General) is usually ID 1 or 2
- Custom topics get auto-incremented IDs
- Store mapping: `{ "topic_name": topic_id }` in config
