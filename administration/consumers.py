import json
from channels.generic.websocket import AsyncWebsocketConsumer

print("\n\n\nExecuted\n\n\n")

class EnrollmentRequestConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        """ Connect user to the WebSocket group """
        
        print("Connected to WebSocket")
        await self.channel_layer.group_add("enrollment_requests", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """ Disconnect user from the WebSocket group """
        print("Disconnected from WebSocket")
        await self.channel_layer.group_discard("enrollment_requests", self.channel_name)

    async def receive(self, text_data):
        """ Handle messages from WebSocket """
        data = json.loads(text_data)
        action = data.get("action")

        if action == "new_enrollment":
            await self.channel_layer.group_send(
                "enrollment_requests",
                {
                    "type": "send_enrollment_update",
                    "message": "A new enrollment request has been added!"
                }
            )

    async def send_enrollment_update(self, event):
        """ Send message to WebSocket """
        await self.send(text_data=json.dumps({"message": event["message"]}))
