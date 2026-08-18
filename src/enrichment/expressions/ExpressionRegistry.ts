/**
 * ExpressionRegistry.ts - Expression Overlay Registry for Meli Visual Enrichment
 *
 * Data-driven registry mapping companion mood states to vector/SVG overlay definitions
 * without regenerating or altering the canonical base face.
 */

export type MeliExpressionId =
  | 'idle'
  | 'curious'
  | 'hover'
  | 'happy'
  | 'blink'
  | 'sleepy'
  | 'thinking'
  | 'focused'
  | 'confused'
  | 'error'
  | 'complete'
  | 'greeting';

export interface ExpressionDefinition {
  id: MeliExpressionId;
  name: string;
  description: string;
  svgUrl: string;
  compositeUrl: string;
  isOverlayOnly: boolean;
  contextualGlassesDefault: boolean;
  defaultHeartColor: string;
}

export const EXPRESSION_REGISTRY: Record<MeliExpressionId, ExpressionDefinition> = {
  idle: {
    id: 'idle',
    name: 'Idle (Canonical)',
    description: 'Pure canonical Meli face preserved untouched.',
    svgUrl: '/expressions/idle.svg',
    compositeUrl: '/idle.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF6B8B',
  },
  curious: {
    id: 'curious',
    name: 'Curious',
    description: 'Raised inner brows, gaze shifted up-left, soft open "o" mouth, curiosity sparkle.',
    svgUrl: '/expressions/curious.svg',
    compositeUrl: '/curious.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FBBF24',
  },
  hover: {
    id: 'hover',
    name: 'Hover (Attentive)',
    description: 'Attentive gaze tracking pointer, alert brow lift, subtle amused smirk.',
    svgUrl: '/expressions/hover.svg',
    compositeUrl: '/hover.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF8DA1',
  },
  happy: {
    id: 'happy',
    name: 'Happy',
    description: 'Gentle crescent smiling eyes, genuine open smile, soft rosy cheek blush.',
    svgUrl: '/expressions/happy.svg',
    compositeUrl: '/happy.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF4081',
  },
  blink: {
    id: 'blink',
    name: 'Blink',
    description: 'Natural eyelid overlay resting over existing eyes.',
    svgUrl: '/expressions/blink.svg',
    compositeUrl: '/blink.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF6B8B',
  },
  sleepy: {
    id: 'sleepy',
    name: 'Sleepy / Low Energy',
    description: 'Heavy droopy eyelids covering top 60% of pupils, low-droop relaxed brows.',
    svgUrl: '/expressions/sleepy.svg',
    compositeUrl: '/sleepy.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#90CAF9',
  },
  thinking: {
    id: 'thinking',
    name: 'Thinking / Processing',
    description: 'Gaze shifted up-right, analytical asymmetric brows, straight thinking mouth.',
    svgUrl: '/expressions/thinking.svg',
    compositeUrl: '/thinking.png',
    isOverlayOnly: true,
    contextualGlassesDefault: true,
    defaultHeartColor: '#B388FF',
  },
  focused: {
    id: 'focused',
    name: 'Focused / Streaming',
    description: 'Narrowed calm eyes, concentrated lower straight brows, firm closed mouth.',
    svgUrl: '/expressions/focused.svg',
    compositeUrl: '/focused.png',
    isOverlayOnly: true,
    contextualGlassesDefault: true,
    defaultHeartColor: '#448AFF',
  },
  confused: {
    id: 'confused',
    name: 'Confused / Questioning',
    description: 'One brow raised high, one brow low, asymmetric questioning mouth.',
    svgUrl: '/expressions/confused.svg',
    compositeUrl: '/confused.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FFB74D',
  },
  error: {
    id: 'error',
    name: 'Error / Concerned',
    description: 'Worried inverted brows (/ \\), concerned downcast gaze, wavy mouth, cyan sweat drop.',
    svgUrl: '/expressions/error.svg',
    compositeUrl: '/error.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF5252',
  },
  complete: {
    id: 'complete',
    name: 'Complete / Triumphant',
    description: 'Bright joyful eyes with star speculars, confident smile, success sparkle star.',
    svgUrl: '/expressions/complete.svg',
    compositeUrl: '/complete.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#69F0AE',
  },
  greeting: {
    id: 'greeting',
    name: 'Greeting / Welcoming',
    description: 'Direct friendly eye contact, welcoming gentle open smile, soft warm blush.',
    svgUrl: '/expressions/greeting.svg',
    compositeUrl: '/greeting.png',
    isOverlayOnly: true,
    contextualGlassesDefault: false,
    defaultHeartColor: '#FF80AB',
  },
};
