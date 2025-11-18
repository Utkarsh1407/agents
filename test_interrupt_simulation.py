import asyncio
from livekit.agents.interrupt_handler import handle_transcript_event, IGNORED_WORDS

# -------------------------------
# Fake Session (for simulation)
# -------------------------------

class FakeSession:
    def __init__(self, speaking=False):
        self._speaking = speaking

    async def is_agent_speaking(self):
        return self._speaking

    async def stop_agent_speaking(self):
        print("[session] Agent speaking stopped")

    async def register_user_transcript(self, text, conf):
        print(f"[session] Registered user transcript: {text} (conf={conf})")


# -------------------------------
# Test Runner
# -------------------------------

async def run_test(text, conf, speaking):
    print("\n--- TEST ---")
    print(f"Input: '{text}', conf={conf}, agent_speaking={speaking}")

    session = FakeSession(speaking=speaking)
    await handle_transcript_event(session, text, conf)


# -------------------------------
# Run All Test Cases
# -------------------------------
async def main():
    print("\n=== TEST 1: filler while agent speaking → ignored ===")
    await run_test("uhh", 0.92, speaking=True)

    print("\n=== TEST 2: filler while agent NOT speaking → registered ===")
    await run_test("uhh", 0.92, speaking=False)

    print("\n=== TEST 3: real word interruption ===")
    await run_test("stop", 0.98, speaking=True)

    print("\n=== TEST 4: low confidence noise → ignored ===")
    await run_test("bla bla", 0.4, speaking=True)

    print("\n=== TEST 5: normal sentence interruption ===")
    await run_test("hey wait a second", 0.97, speaking=True)

asyncio.run(main())