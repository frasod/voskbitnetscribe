"""
Architecture visualization - layer dependencies.
Run this to generate dependency diagram.
"""

def print_architecture():
    diagram = """
╔════════════════════════════════════════════════════════════════╗
║                    VOSK BitNet Scribe Architecture              ║
║                    (Braun-Inspired Clean Design)                ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ ENTRY POINT (main.py)                                           │
│ • Configuration loading                                         │
│ • Validation                                                    │
│ • Application bootstrapping                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (src/ui/)                                    │
│ ┌─────────────┐  ┌─────────────┐  ┌────────────────┐          │
│ │ main_window │  │  styles     │  │  components    │          │
│ │  (PyQt6)    │  │  (Braun)    │  │  (reusable)    │          │
│ └──────┬──────┘  └─────────────┘  └────────────────┘          │
│        │ Delegates to services (never contains logic)           │
└────────┼─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE LAYER (src/services/)                                   │
│ ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐       │
│ │AudioService  │  │InferenceService │  │Clipboard     │       │
│ │  • VOSK      │  │  • BitNet       │  │Service       │       │
│ │  • Recording │  │  • Processing   │  │  • System    │       │
│ └──────┬───────┘  └────────┬────────┘  └──────────────┘       │
│        │                   │                                     │
│        │ Uses contracts    │                                     │
└────────┼───────────────────┼─────────────────────────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ CORE LAYER (src/core/)                                          │
│ ┌──────────────────┐  ┌────────────────────────────┐           │
│ │ models.py        │  │ config.py                  │           │
│ │ • Data contracts │  │ • Configuration            │           │
│ │ • Immutable      │  │ • Validation               │           │
│ │ • Type-safe      │  │ • Environment-based        │           │
│ └──────────────────┘  └────────────────────────────┘           │
│                                                                  │
│ NO DEPENDENCIES (pure domain logic)                             │
└─────────────────────────────────────────────────────────────────┘

DEPENDENCY FLOW (arrows point to dependencies):
    
    main.py
       │
       ├──► core/config.py
       │       │
       │       └──► core/models.py
       │
       └──► ui/main_window.py
               │
               ├──► ui/styles.py ──► core/config.py
               │
               ├──► services/audio_service.py
               │       │
               │       └──► core/models.py
               │
               ├──► services/inference_service.py
               │       │
               │       └──► core/models.py
               │
               └──► services/clipboard_service.py

KEY PRINCIPLES:

✓ SEPARATION: Each layer has single responsibility
✓ DEPENDENCY: Always points inward (UI → Services → Core)
✓ TESTABILITY: Core and Services testable without UI
✓ IMMUTABILITY: Data contracts are frozen
✓ CONTRACTS: Structured results, never exceptions for business logic
✓ BRAUN: Minimal, purposeful, elegant

COMPARISON TO ORIGINAL:

BEFORE:                          AFTER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All in one file (800 lines)  →  Modular layers
Mixed concerns               →  Clear separation  
Hard-coded config           →  Environment-driven
Thrown exceptions           →  Structured results
35% dead code               →  0% waste
Tight coupling              →  Loose coupling
Untestable                  →  Fully testable
Dangerous threading         →  Safe cleanup
"""
    print(diagram)

if __name__ == "__main__":
    print_architecture()
