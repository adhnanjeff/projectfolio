import socket
import json
import asyncio
from config import *
from ids import AdvancedIDS

class SimulinkCANInterface:
    def __init__(self, port=8888):
        self.port = port
        self.socket = None
        self.ids = AdvancedIDS()
        self.running = False
        
    async def start_server(self):
        """Start async TCP server for Simulink communication"""
        server = await asyncio.start_server(
            self.handle_client, 'localhost', self.port
        )
        self.running = True
        
        print(f"🔗 Simulink interface listening on port {self.port}")
        
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """Handle async Simulink client connection"""
        while self.running:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                    
                # Parse CAN message from Simulink
                msg_data = json.loads(data.decode())
                result = await self.process_can_message(msg_data)
                
                # Send result back to Simulink
                writer.write(json.dumps(result).encode())
                await writer.drain()
                
            except Exception as e:
                print(f"Error: {e}")
                break
        writer.close()
        await writer.wait_closed()
    
    async def process_can_message(self, msg_data):
        """Process CAN message and return IDS result"""
        # Extract features and predict
        features = [msg_data['id']] + msg_data['data'][:8]
        # Pad to 9 features if needed
        features = (features + [0]*9)[:9]
        prediction = await asyncio.get_event_loop().run_in_executor(
            None, self.ids.model.predict, [features]
        )
        
        return {
            'anomaly': prediction[0] == -1,
            'attack_type': 'DOS' if prediction[0] == -1 else 'NORMAL',
            'confidence': 0.95
        }

async def main():
    interface = SimulinkCANInterface()
    await interface.start_server()

if __name__ == "__main__":
    asyncio.run(main())