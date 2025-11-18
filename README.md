# LiveKit Interrupt Handler — Real-Time Filler & Interruption Detection
**Author:** Utkarsh Kumar  
**Branch:** `feature/livekit-interrupt-handler-Utkarsh`

---

## 📌 Overview
This feature adds a custom **Interrupt Handler** to LiveKit Agents, allowing the agent to distinguish between:

- **Filler speech** (e.g., "uhh", "hmm", "umm")
- **Low-confidence noise**
- **Meaningful real interruptions** (e.g., "stop", "wait", "hold on")
- **Normal user speech when the agent is silent**

The handler works end-to-end with real-time audio and was tested using the LiveKit basic voice agent.

The implementation ensures the agent:

- Ignores filler and noise  
- Does not get falsely interrupted  
- Immediately stops speaking on meaningful barge-ins  
- Correctly registers real user speech  

This implementation also solves a major issue in basic LiveKit agents where `session.is_agent_speaking()` never returns `true`.  
A robust fix is implemented using reliable session events.

---

## 🔧 What Changed

### 1. Added a New Module  
`livekit/agents/interrupt_handler.py`

This module includes:

- Token normalization  
- Filler detection logic  
- Confidence thresholding  
- Interruption detection  
- A global speaking flag  
- Event-based update mechanism for agent speaking state  
- A locked async handler to avoid race conditions in real-time audio  

---

### 2. New Parameters Introduced

| Parameter | Purpose |
|----------|---------|
| `IGNORED_WORDS` | Configurable filler word list |
| `INTERRUPT_WORDS` | Words that always trigger interruption |
| `MIN_CONF` | STT noise threshold |
| `AGENT_SPEAKING_FLAG` | Real-time speaking state |
| `update_speaking_flag()` | Event-driven speaking-state updater |

---

### 3. Modifications to Basic Agent Example

Inside `examples/voice_agents/basic_agent.py`, the following listeners and bridges were added:

- `response_generated`
- `response_completed`
- `transcription`
- `stt`
- Bridge routing all live transcripts into `handle_transcript_event()`

These changes allow the interrupt handler to integrate perfectly with real-time speech.

---

## 🧪 What Works

### ✔ Real-Time Filler Detection
Filler-only inputs like **"uhh", "hmm", "umm"** while the agent is speaking are ignored.

### ✔ Low Confidence Noise Ignored  
Inputs with very low STT confidence (breath noises, mic pops, rustling) are discarded.

### ✔ Real Interruptions Work Reliably  
Words such as **"stop"**, **"wait"**, **"hold on"** immediately stop TTS output and register the transcript.

### ✔ Accurate Speaking State  
Because most TTS engines (like Cartesia) do not emit speaking signals, the system uses:

# 🎙️ Real-Time Interrupt Handler for LiveKit Agents

This module introduces a **production-ready interrupt handling system** for LiveKit voice agents.  
It reliably distinguishes **meaningful user interruptions** from fillers, noise, and low-confidence transcripts—allowing smooth conversational experiences without depending on TTS-specific events.

---

## ⚠️ Known Issues / Edge Cases

### 1. TTS providers not emitting `agent_speaking` events
Some TTS engines don’t send the `agent_speaking` event.  
✅ This implementation bypasses the issue by detecting **LLM-generated responses directly**.

### 2. Very fast interruptions (<150ms)
If the user speaks immediately after silence, STT may produce empty or low-confidence text.  
✅ Handled by **ignoring `text=""` and confidence < `MIN_CONF`**.

### 3. Multi-word interrupt phrases
Phrases like **“hold on”** are detected correctly.  
⚠️ Language variations may require simple configuration updates.

---

## 🚀 Steps to Test the Feature

### **1. Start the Agent**
```bash
python examples/voice_agents/basic_agent.py
```

## 2. Test Filler During Agent Speech

While the agent is talking, say:
- uhh  
- umm  
- hmm  
- haan  

**Expected result:**
- No interruption  
- Handler prints:  
  > “Filler during agent speech → ignored”

---

## 3. Test Meaningful Interruptions

Say:
- stop  
- wait  
- hold on  
- no no stop  

**Expected result:**
- TTS immediately stops  
- Transcript registered  
- Handler prints:  
  > “Meaningful interruption → stopping agent”

---

## 4. Test Low Confidence Noise

Blow into mic or rustle paper.

**Expected result:**
- Handler prints:  
  > “Low confidence → ignored”

---

## 5. Test Normal User Input

Speak after agent finishes:
- what is the weather  
- tell me something  
- okay continue  

**Expected result:**
- Transcript registered normally  
- Agent responds with new TTS output

---

## 🖥 Environment Details

- **Python:** 3.9  
- **LiveKit Agents:** Latest local clone (Nov 2025)

### Dependencies
- deepgram/nova-3 (STT)  
- openai/gpt-4.1-mini (LLM)  
- cartesia/sonic-2 (TTS)  
- silero VAD  
- Multilingual turn detector  

---

## 📚 Summary

This feature adds a production-ready interrupt handling system to LiveKit Agents that:

- Differentiates real speech from filler/noise  
- Supports barge-in interruption  
- Works reliably with real-time audio inputs  
- Avoids dependency on TTS-provider-specific events  
- Integrates directly into the existing session model  

The system has been **validated end-to-end** and is ready for merge.


