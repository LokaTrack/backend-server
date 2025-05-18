import json
import binascii
import logging
from Crypto.Util.strxor import strxor
import struct
import os

logger = logging.getLogger(__name__)

MQTT_ENCRYPT_KEY = os.getenv("MQTT_ENCRYPT_KEY")
HEX_KEY = bytes.fromhex(MQTT_ENCRYPT_KEY)

def decrypt_message(encrypted_hex_message: str, key=HEX_KEY):
    """
    Decrypts a hex-encoded ChaCha20 encrypted message.
    Args:
        encrypted_hex_message (str): The hex-encoded encrypted message.
        key (bytes): The 256-bit key for decryption. Default is a predefined key.
    Returns:
        dict: The decrypted JSON payload.
    Raises:
        UnicodeDecodeError: If the decrypted bytes cannot be decoded as UTF-8.
        json.JSONDecodeError: If the decrypted message is not valid JSON.
    """

    def quarter_round(state, a, b, c, d):
        """ChaCha20 quarter round function"""
        # a += b; d ^= a; d <<<= 16
        state[a] = (state[a] + state[b]) & 0xFFFFFFFF
        state[d] ^= state[a]
        state[d] = ((state[d] << 16) | (state[d] >> 16)) & 0xFFFFFFFF

        # c += d; b ^= c; b <<<= 12
        state[c] = (state[c] + state[d]) & 0xFFFFFFFF
        state[b] ^= state[c]
        state[b] = ((state[b] << 12) | (state[b] >> 20)) & 0xFFFFFFFF

        # a += b; d ^= a; d <<<= 8
        state[a] = (state[a] + state[b]) & 0xFFFFFFFF
        state[d] ^= state[a]
        state[d] = ((state[d] << 8) | (state[d] >> 24)) & 0xFFFFFFFF

        # c += d; b ^= c; b <<<= 7
        state[c] = (state[c] + state[d]) & 0xFFFFFFFF
        state[b] ^= state[c]
        state[b] = ((state[b] << 7) | (state[b] >> 25)) & 0xFFFFFFFF

        return state

    def chacha20_block(key, counter_value, nonce):
        """Generate a ChaCha20 block"""
        # Constants for ChaCha20
        CONSTANTS = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

        # Create initial state
        state = CONSTANTS[:]  # Copy the constants

        # Add key words (8 for 256-bit key)
        for i in range(8):
            state.append(struct.unpack("<I", key[i * 4 : i * 4 + 4])[0])

        # Add counter and nonce
        state.append(counter_value & 0xFFFFFFFF)  # Lower 32 bits of counter
        state.append((counter_value >> 32) & 0xFFFFFFFF)  # Upper 32 bits of counter
        state.append(struct.unpack("<I", nonce[:4])[0])
        state.append(struct.unpack("<I", nonce[4:8])[0])

        # Copy initial state
        working_state = state[:]

        # ChaCha20 rounds (20 rounds = 10 iterations of double round)
        for _ in range(10):
            # Column round
            working_state = quarter_round(working_state, 0, 4, 8, 12)
            working_state = quarter_round(working_state, 1, 5, 9, 13)
            working_state = quarter_round(working_state, 2, 6, 10, 14)
            working_state = quarter_round(working_state, 3, 7, 11, 15)

            # Diagonal round
            working_state = quarter_round(working_state, 0, 5, 10, 15)
            working_state = quarter_round(working_state, 1, 6, 11, 12)
            working_state = quarter_round(working_state, 2, 7, 8, 13)
            working_state = quarter_round(working_state, 3, 4, 9, 14)

        # Add working state to initial state
        for i in range(16):
            state[i] = (state[i] + working_state[i]) & 0xFFFFFFFF

        # Convert state to bytes
        result = bytearray(64)
        for i in range(16):
            struct.pack_into("<I", result, i * 4, state[i])

        return bytes(result)

    try:
        encrypted_message = binascii.unhexlify(encrypted_hex_message)

        iv = encrypted_message[:8]
        counter_bytes = encrypted_message[8:16]
        ciphertext = encrypted_message[16:]

        # logger.debug(f"IV: {iv.hex()}")
        # logger.debug(f"Counter: {counter_bytes.hex()}")
        # logger.debug(f"Ciphertext: {ciphertext.hex()}")
        # logger.debug(f"Ciphertext length: {len(ciphertext)} bytes")

        # Get the starting counter value as a 64-bit integer
        counter_value = int.from_bytes(counter_bytes, byteorder="little")

        # Create an empty buffer for the keystream
        keystream = bytearray()

        # Generate keystream blocks for each 64-byte chunk of ciphertext
        blocks_needed = (len(ciphertext) + 63) // 64  # Ceiling division

        for block in range(blocks_needed):
            # Generate keystream block with current counter value
            keystream_block = chacha20_block(key, counter_value + block, iv)
            keystream.extend(keystream_block)

        # Trim keystream to match ciphertext length
        keystream = keystream[: len(ciphertext)]

        # XOR keystream with ciphertext to get plaintext
        decrypted_bytes = strxor(ciphertext, keystream)

        try:
            # Try to decode as UTF-8
            decrypted_message = decrypted_bytes.decode("utf-8")
            logger.debug(f"Decrypted message: {decrypted_message}")

            # Try to parse as JSON
            decrypted_payload = json.loads(decrypted_message)
            return decrypted_payload
        except UnicodeDecodeError as e:
            # If UTF-8 decoding fails, log the error and hex dump for debugging
            logger.error(f"UTF-8 decode error: {e}")
            logger.debug(f"Decrypted hex: {decrypted_bytes.hex()}")
            logger.debug(f"First 100 bytes: {decrypted_bytes[:100].hex()}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"Decrypted text: {decrypted_message}")
            raise

    except Exception as e:
        logger.error(f"Error decrypting message: {e}")
        return None
