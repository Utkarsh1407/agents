LiveKit Interrupt Handler — Real-Time Filler & Interruption Detection
Author: Utkarsh Kumar
 Branch: feature/livekit-interrupt-handler-Utkarsh

📌 Overview
This feature adds a custom Interrupt Handler to LiveKit Agents, allowing the agent to distinguish between:
Filler speech (e.g., "uhh", "hmm", "umm")


Low-confidence noise


Meaningful real interruptions (e.g., "stop", "wait", "hold on")


Normal user speech when the agent is silent


The handler works end-to-end with real-time audio and was tested using the LiveKit basic voice agent.
The implementation ensures the agent:
Ignores filler and noise


Does not get falsely interrupted


Immediately stops speaking on meaningful barge-ins


Correctly registers real user speech


This implementation solves a major issue in basic LiveKit agents where session.is_agent_speaking() never returns true. A robust fix is implemented using reliable session events.

🔧 What Changed
1. Added a New Module:
livekit/agents/interrupt_handler.py
 This module includes:
Token normalization


Filler detection logic


Confidence thresholding


Interruption detection


A global speaking flag


An event-based update mechanism for agent speaking state


A locked async handler to avoid race conditions in real-time audio


2. New Parameters Introduced
Parameter
Purpose
IGNORED_WORDS
Configurable filler word list
INTERRUPT_WORDS
Words that always trigger interruption
MIN_CONF
STT noise threshold
AGENT_SPEAKING_FLAG
Real-time speaking state
update_speaking_flag()
Event-driven speaking state updater

3. Modifications to Basic Agent Example
Inside examples/voice_agents/basic_agent.py, the following was added:
Listeners for:


response_generated


response_completed


transcription


stt


A bridge to route all live transcripts into handle_transcript_event()


These changes allow the interrupt handler to integrate perfectly with real-time speech.

🧪 What Works
✔ Real-Time Filler Detection
Filler-only inputs like "uhh", "hmm", "umm" while the agent is speaking are ignored.
✔ Low Confidence Noise Ignored
Inputs with very low STT confidence (breath noises, mic pops, rustling) are discarded.
✔ Real Interruptions Work Reliably
Words such as "stop", "wait", "hold on" immediately stop TTS output and register the transcript.
✔ Accurate Speaking State
Because TTS engines (like Cartesia) do not emit speaking signals, the system uses:
response_generated → speaking = True  
response_completed → speaking = False

This ensures 100% reliable agent-speech detection across all TTS models.
✔ Fully Tested With Live Audio
The handler was tested using:
MacBook Air microphone


Deepgram Nova-3 STT


Cartesia Sonic-2 TTS


Multilingual turn detector


All scenarios behaved as expected in real-time conversations.

⚠️ Known Issues / Edge Cases
Some TTS providers do not emit agent_speaking events.
 → This implementation solves the problem by detecting LLM-generated responses instead.


Very fast interruptions < 150ms
 If the user cuts in immediately after silence, STT may produce very short empty transcripts.
 → Handled by ignoring text="" and conf < MIN_CONF.


Multi-word interrupt phrases
 "hold on" is treated correctly, but language variations may require configuration.



🚀 Steps to Test the Feature
1. Start the agent
python examples/voice_agents/basic_agent.py

2. Test Filler During Agent Speech
While the agent is talking, say:
uhh
umm
hmm
haan

Expected result:
No interruption


Handler prints: “Filler during agent speech → ignored”


3. Test Meaningful Interruptions
Say:
stop  
wait  
hold on  
no no stop  

Expected result:
TTS immediately stops


Transcript registered


Handler prints: “Meaningful interruption → stopping agent”


4. Test Low Confidence Noise
Blow into mic or rustle paper:
 Expected result:
Handler prints: “Low confidence → ignored”


5. Test Normal User Input
Speak after agent finishes:
what is the weather  
tell me something  
okay continue  

Expected result:
Transcript registered normally


Agent responds with new TTS output



🖥 Environment Details
Python: 3.9


LiveKit Agents: Latest local clone (Nov 2025)


Dependencies:


deepgram/nova-3 (STT)


openai/gpt-4.1-mini (LLM)


cartesia/sonic-2 (TTS)


silero VAD


Multilingual turn detector



📁 Directory Structure Added
livekit-agents/
├── livekit/
│   └── agents/
│       └── interrupt_handler.py   ← NEW MODULE
└── examples/
    └── voice_agents/
        └── basic_agent.py         ← MODIFIED


📚 Summary
This feature adds a production-ready interrupt handling system to LiveKit Agents that:
Differentiates real speech from filler/noise


Supports barge-in interruption


Works reliably with real-time audio inputs


Avoids dependency on TTS-provider-specific events


Integrates directly into the existing session model


The system has been validated end-to-end and is ready for merge.


