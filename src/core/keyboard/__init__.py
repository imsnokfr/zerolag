"""
Keyboard Module for ZeroLag

This module provides advanced keyboard optimizations including:
- Anti-ghosting and NKRO simulation
- Key combination detection
- Gaming-specific optimizations
- Real-time key state management

Main Components:
- AntiGhostingEngine: Main engine for anti-ghosting and NKRO
- NKROSimulator: N-Key Rollover simulation
- KeyMatrix: Physical key matrix for ghosting detection
- KeyCombination: Key combination detection and management
"""

from .anti_ghosting import (
    AntiGhostingEngine,
    NKROSimulator,
    KeyMatrix,
    KeyCombination,
    KeyInfo,
    KeyState,
    GhostingType,
    AntiGhostingStats
)
from .rapid_actions import (
    RapidActionsEngine,
    RapidTrigger,
    SnapTap,
    TurboMode,
    AdaptiveResponse,
    ActuationEmulation,
    RapidActionType,
    KeyVelocity,
    RapidActionStats,
    RapidTriggerConfig,
    SnapTapConfig,
    TurboModeConfig,
    AdaptiveResponseConfig,
    ActuationEmulationConfig
)
from .rapid_actions_integration import (
    RapidActionsIntegration,
    RapidActionsIntegrationConfig,
    RapidActionsIntegrationStats
)

__all__ = [
    # Anti-ghosting components
    'AntiGhostingEngine',
    'NKROSimulator',
    'KeyMatrix',
    'KeyCombination',
    'KeyInfo',
    'KeyState',
    'GhostingType',
    'AntiGhostingStats',
    
    # Rapid actions components
    'RapidActionsEngine',
    'RapidTrigger',
    'SnapTap',
    'TurboMode',
    'AdaptiveResponse',
    'ActuationEmulation',
    'RapidActionType',
    'KeyVelocity',
    'RapidActionStats',
    'RapidTriggerConfig',
    'SnapTapConfig',
    'TurboModeConfig',
    'AdaptiveResponseConfig',
    'ActuationEmulationConfig',
    
    # Integration components
    'RapidActionsIntegration',
    'RapidActionsIntegrationConfig',
    'RapidActionsIntegrationStats'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Anti-ghosting and NKRO simulation for ZeroLag gaming input optimization"
