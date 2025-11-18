import logging
import asyncio
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    room_io,
)
from livekit.agents.llm import function_tool
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import silero

# Import your custom handler and helpers from the local file
from livekit.agents.interrupt_handler import (
    handle_transcript_event,
    normalize_text,
    tokenize,
    is_filler_sequence,
    MIN_CONFIDENCE
)

load_dotenv()
logger = logging.getLogger("agent")


class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "Your name is Kelly. Keep responses short. "
                "Speak English. No emojis."
            )
        )
        self.is_agent_speaking = False  # Manual flag initialized

    async def on_enter(self):
        self.session.generate_reply()

    # The SDK automatically calls these methods if they are defined on the Agent class.
    
    def on_speech_start(self, ev):
        self.is_agent_speaking = True

    def on_speech_end(self, ev):
        self.is_agent_speaking = False
        
    @function_tool
    async def lookup_weather(self, ctx: RunContext, location: str, latitude: str, longitude: str):
        return "sunny with 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):

    # Instantiate the agent outside of session.start
    my_agent_instance = MyAgent()
    
    session = AgentSession(
        stt="deepgram/nova-3",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",

        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],

        # Enable false interruption resume and set timeout to instant
        preemptive_generation=False,
        resume_false_interruption=True,
        false_interruption_timeout=0.0,
    )

    @session.on("transcription")
    def _on_transcription(ev):

        alts = getattr(ev, "alternatives", None)
        if alts and len(alts) > 0:
            alt = alts[0]
            text = getattr(alt, "text", "") or ""
            conf = getattr(alt, "confidence", 1.0)
        else:
            text = getattr(ev, "text", "") or ""
            conf = getattr(ev, "confidence", 1.0)

        print(f"[TRANSCRIPTION] {text!r} conf={conf}")

        # Pass the agent instance to the handler
        asyncio.create_task(handle_transcript_event(session, text, conf, my_agent_instance))

    # -----------------------------------------------------------
    # STT FALLBACK EVENT (Pass the agent instance)
    # -----------------------------------------------------------
    @session.on("stt")
    def _on_stt(ev):
        text = getattr(ev, "text", "") or ""
        conf = getattr(ev, "confidence", 1.0)
        print(f"[STT] {text!r} conf={conf}")

        # Pass the agent instance to the handler
        asyncio.create_task(handle_transcript_event(session, text, conf, my_agent_instance))

    # -----------------------------------------------------------
    # USER UTTERANCE END (Used for filtering LLM input)
    # -----------------------------------------------------------
    @session.on("user_utterance_end")
    def _on_utterance_end(ev):
        text = getattr(ev, "text", "") or ""
        conf = getattr(ev, "confidence", 1.0)
        
        t = normalize_text(text)
        
        # 1. Check for empty, low confidence, or pure filler
        is_filler = (
            not t or 
            conf < MIN_CONFIDENCE or 
            is_filler_sequence(tokenize(t))
        )
        
        if is_filler:
            print("[LLM_IGNORED] reason=filtered by custom logic (filler/low confidence)")
            session.set_action("ignore") # Explicitly prevent LLM reply
            return
        
        # If it reaches here, the utterance is valid and will be sent to the LLM
        print(f"[LLM_PROCESSED] reason=real speech text='{t}'")


    await session.start(
        agent=my_agent_instance, # Use the instantiated agent
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions()
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)