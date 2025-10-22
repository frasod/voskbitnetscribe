# Chat Feature Added

## Overview
Added a text-based chatbot interface to the VOSK BitNet Scribe application. The chat runs alongside the voice transcription feature in a tabbed interface.

## New Components

### ChatService (`src/services/chat_service.py`)
- Handles conversational interactions with BitNet
- Maintains conversation history for context
- Supports cancellation and history management
- Thread-safe implementation using Qt signals

### UI Updates (`src/ui/main_window.py`)
- Added tabbed interface with two tabs:
  1. **Voice Transcription** - Original voice-to-text functionality
  2. **Chat** - New text-based chat interface
- Chat interface includes:
  - Chat history display (read-only text area)
  - Message input field (press Enter or click Send)
  - Clear History button
  - Copy Chat button
  - Status indicator

### ChatWorker
- Background QThread worker for non-blocking chat requests
- Emits signals for status updates and completion
- Prevents UI freezing during API calls

## Features

1. **Conversational Context**: Chat maintains conversation history (last 10 messages)
2. **Thread-Safe**: All UI updates happen via Qt signals
3. **Non-Blocking**: Chat runs in background thread
4. **Keyboard Support**: Press Enter to send messages
5. **History Management**: Clear conversation history anytime
6. **Copy Support**: Copy entire chat history to clipboard

## Usage

1. Launch the application
2. Click the "Chat" tab at the top
3. Type your message in the input field
4. Press Enter or click "Send"
5. The assistant's response will appear in the chat history

## Technical Notes

- Uses same BitNet endpoint as note generation (`http://localhost:8081/completion`)
- Conversation history kept in memory (cleared on restart)
- Responses are parsed from multiple JSON formats for compatibility
- Stop tokens prevent response overflow (`\nUser:`, `\n\n`)

## Architecture
- Clean separation: ChatService handles logic, UI handles presentation
- Follows existing patterns: Worker threads, signal/slot communication
- Zero technical debt: Immutable messages, proper error handling
