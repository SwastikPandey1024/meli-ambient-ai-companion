/**
 * CharacterAssetManifest Typed Specification
 * Defines the static raster/vector asset registration contract and motion envelope for Meli.
 */

export type MeliMoodState =
  | 'base'
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

export type AssetCategory = 'base_layer' | 'expression_overlay';

export interface Point2D {
  readonly x: number;
  readonly y: number;
  readonly description?: string;
}

export interface Dimension2D {
  readonly width: number;
  readonly height: number;
  readonly unit?: 'px';
}

export interface BoundingBoxSpec {
  readonly min_x: number;
  readonly min_y: number;
  readonly max_x: number;
  readonly max_y: number;
  readonly width?: number;
  readonly height?: number;
  readonly safe_margin_px: number;
}

export interface MotionStateSpec {
  readonly max_translation_px?: number;
  readonly translate_y_max_px?: number;
  readonly max_rotation_deg: number;
  readonly scale_y?: number;
  readonly scale_x?: number;
}

export interface MotionEnvelopeSpec {
  readonly max_translation_px: number; // Max global limit: 4.0px
  readonly max_rotation_deg: number;   // Max global limit: 2.0 deg
  readonly states: Record<string, MotionStateSpec>;
}

export interface PersonaMetadataSpec {
  readonly demographic: 'Young Adult — 18+';
  readonly archetype: string;
  readonly tone: string;
}

export interface GlobalGeometrySpec {
  readonly reference_canvas: Dimension2D;
  readonly master_canvas: Dimension2D;
  readonly safety_margin_px: number;
  readonly bounding_box: BoundingBoxSpec;
  readonly anchors: {
    readonly gaze_anchor: Point2D;
    readonly signal_heart_anchor: Point2D;
    readonly grounding_anchor: Point2D;
  };
  readonly motion_envelope: MotionEnvelopeSpec;
}

export interface TechnicalRequirementsSpec {
  readonly primary_format: string;
  readonly runtime_format: string;
  readonly color_profile: string;
  readonly alpha_handling: string;
  readonly background: string;
}

export interface CharacterAssetEntry {
  readonly id: string;
  readonly filename: string;
  readonly category: AssetCategory;
  readonly mood_state: MeliMoodState;
  readonly description: string;
  readonly canvas_size: Dimension2D;
  readonly transparency_requirement: string;
  readonly gaze_anchor: Point2D;
  readonly signal_heart_anchor: Point2D;
  readonly grounding_anchor: Point2D;
  readonly bounding_box: BoundingBoxSpec;
  readonly status: 'planned' | 'ready' | 'deprecated';
}

export interface CharacterAssetManifest {
  readonly $schema?: string;
  readonly schema_version: string;
  readonly character: string;
  readonly persona_metadata: PersonaMetadataSpec;
  readonly description: string;
  readonly canonical_reference: string;
  readonly global_geometry: GlobalGeometrySpec;
  readonly technical_requirements: TechnicalRequirementsSpec;
  readonly assets: readonly CharacterAssetEntry[];
}
