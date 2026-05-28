import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ScrutinResultsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.scrutin_slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"scrutin_{self.scrutin_slug}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def vote_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "vote_update",
                    "scrutin_slug": self.scrutin_slug,
                    "payload": event["payload"],
                },
            ),
        )
