import numpy as np

message1 = "30CD424".encode().ljust(13, b'\x00')
message2 = "3169C62".encode().ljust(13, b'\x00')
message3 = "This is a testing message of Xin Yao from University of Florida, Electrical and Computer Engineering Department! [TESTING]!!".encode()

message = message1 + message2 + message3
byte_array = np.frombuffer(message, dtype=np.uint8)
bits = np.unpackbits(byte_array)  # numpy array of bits
print("Message: ", message, type(message), len(message))
print("Packet length: ", len(byte_array), type(byte_array), '\n')
print("Packet bits length: ", len(bits), type(bits[0]), '\n')


decoded_message_1 = message[0:13].rstrip(b'\x00').decode('utf-8')
decoded_message_2 = message[13:26].rstrip(b'\x00').decode('utf-8')
decoded_message_3 = message[26:].decode('utf-8')

print(decoded_message_1, len(decoded_message_1))
print(decoded_message_2, len(decoded_message_2))
print(decoded_message_3, len(decoded_message_3))
