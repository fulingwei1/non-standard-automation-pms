import { AbsoluteFill, Sequence } from 'remotion';
import { VIDEO_CONFIG } from './config';
import {
  OpeningScene,
  PainPointsScene,
  CapabilitiesScene,
  HighlightsScene,
  EndingScene,
} from './scenes';

/**
 * 产品宣传视频主组件
 *
 * 视频结构：
 * - 0-5秒: 开场动画
 * - 5-20秒: 痛点引入
 * - 20-60秒: 核心能力展示
 * - 60-75秒: 技术亮点
 * - 75-90秒: 结尾
 */
export const PromoVideo: React.FC = () => {
  const { scenes } = VIDEO_CONFIG;

  return (
    <AbsoluteFill>
      {/* 场景1: 开场 */}
      <Sequence from={scenes.opening.start} durationInFrames={scenes.opening.duration}>
        <OpeningScene />
      </Sequence>

      {/* 场景2: 痛点引入 */}
      <Sequence from={scenes.painPoints.start} durationInFrames={scenes.painPoints.duration}>
        <PainPointsScene />
      </Sequence>

      {/* 场景3: 核心能力展示 */}
      <Sequence from={scenes.capabilities.start} durationInFrames={scenes.capabilities.duration}>
        <CapabilitiesScene />
      </Sequence>

      {/* 场景4: 技术亮点 */}
      <Sequence from={scenes.highlights.start} durationInFrames={scenes.highlights.duration}>
        <HighlightsScene />
      </Sequence>

      {/* 场景5: 结尾 */}
      <Sequence from={scenes.ending.start} durationInFrames={scenes.ending.duration}>
        <EndingScene />
      </Sequence>
    </AbsoluteFill>
  );
};
