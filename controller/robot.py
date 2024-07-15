import json

# Command DTO (Data Transfer Object)
class Command:
    def __init__(self, command: str, value: str):
        self.command = command
        self.value = value

class RobotController:
    def __init__(self, client, action_topic, listen_topic):
        self.client = client
        self.client.on_message = self.on_message

        self.action_topic = action_topic
        self.listen_topic = listen_topic
        
        self.client.subscribe(listen_topic)
        # check if the client is connected otherwise exit
        self.client.loop_start()
        
    def on_message(self, client, userdata, message):
        print(f"Received `{message.payload.decode()}` from `{message.topic}` topic")
        
    
    def send_command(self, cmd: Command):
        # convert command to json and publish to the topic
        data = json.dumps(cmd.__dict__)
        self.client.publish(self.action_topic, data)
        
    def move_forward(self):
        self.send_command(Command("move", "F"))
        
    def move_backward(self):
        self.send_command(Command("move", "B"))
        
    def turn_left(self):
        self.send_command(Command("move", "L"))
        
    def turn_right(self):
        self.send_command(Command("move", "R"))