/**
 * PerformanceAssetManager.ts — Complete Standalone Performance Asset Resolver
 *
 * Architecture:
 * - Maps mood states and companion events directly to complete standalone illustrations.
 * - Zero facial delta overlays / zero compositing layers.
 * - Preloads all 16 frozen runtime PNGs for 0-latency instant cross-fading.
 */

export type MeliPerformanceState =
  | 'idle'
  | 'curious'
  | 'happy'
  | 'thinking'
  | 'working'
  | 'focused'
  | 'sleepy'
  | 'confused'
  | 'surprised'
  | 'error'
  | 'complete'
  | 'greeting'
  | 'celebration'
  | 'proximity'
  | 'hover'
  | 'click_pet';

export const PERFORMANCE_ASSET_MAP: Record<MeliPerformanceState, string> = {
  idle: '/states/meli_idle.png',
  curious: '/states/meli_curious.png',
  happy: '/states/meli_happy.png',
  thinking: '/states/meli_thinking.png',
  working: '/states/meli_working.png',
  focused: '/states/meli_focused.png',
  sleepy: '/states/meli_sleepy.png',
  confused: '/states/meli_confused.png',
  surprised: '/states/meli_surprised.png',
  error: '/states/meli_error.png',
  complete: '/states/meli_complete.png',
  greeting: '/states/meli_greeting.png',
  celebration: '/special/meli_celebration.png',
  proximity: '/special/meli_proximity.png',
  hover: '/special/meli_hover.png',
  click_pet: '/special/meli_click_pet.png',
};

/**
 * Maps system and companion events to the canonical performance state.
 */
export function resolvePerformanceState(eventOrMood: string): MeliPerformanceState {
  const key = eventOrMood.toUpperCase().trim();
  switch (key) {
    case 'THINKING':
    case 'REASONING':
      return 'thinking';

    case 'MEMORY_RETRIEVED':
    case 'CURIOUS':
    case 'SEARCHING':
      return 'curious';

    case 'RESPONSE_STREAM':
    case 'STREAMING':
    case 'FOCUSED':
    case 'BUSY':
      return 'focused';

    case 'WORKING':
      return 'working';

    case 'RESPONSE_COMPLETED':
    case 'COMPLETE':
    case 'SUCCESS':
      return 'complete';

    case 'ERROR':
    case 'WARNING':
    case 'FAILED':
      return 'error';

    case 'APP_LAUNCH':
    case 'GREETING':
    case 'WELCOME':
      return 'greeting';

    case 'SLEEP':
    case 'SLEEPY':
    case 'REST':
      return 'sleepy';

    case 'HOVER':
      return 'hover';

    case 'CLICK':
    case 'CLICK_PET':
      return 'click_pet';

    case 'HAPPY':
    case 'PET':
      return 'happy';

    case 'PROXIMITY':
      return 'proximity';

    case 'CONFUSED':
      return 'confused';

    case 'SURPRISED':
      return 'surprised';

    case 'CELEBRATION':
    case 'VICTORY':
    case 'TASK_COMPLETE':
      return 'celebration';

    case 'IDLE':
    default:
      return 'idle';
  }
}

/**
 * Returns the resolved image path for a given performance state or event.
 */
export function getPerformanceAssetPath(eventOrMood: string): string {
  const state = resolvePerformanceState(eventOrMood);
  return PERFORMANCE_ASSET_MAP[state] || PERFORMANCE_ASSET_MAP.idle;
}

/**
 * Proactively preloads all 16 runtime illustrations into memory for instantaneous transitions.
 */
export function preloadAllPerformanceAssets(): void {
  if (typeof window === 'undefined') return;
  Object.values(PERFORMANCE_ASSET_MAP).forEach((src) => {
    const img = new Image();
    img.src = src;
  });
}
