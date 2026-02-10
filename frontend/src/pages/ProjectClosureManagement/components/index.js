/**
 * 项目结项管理页面 - 组件统一导出
 *
 * 【架构说明】
 * 页面级组件（ProjectSelectionView, ProjectClosureContent 等）定义在本目录中，仅供本页面使用。
 * 对话框组件（CreateClosureDialog, ReviewClosureDialog 等）请从
 * components/project-closure/ 直接导入，避免页面级重复 re-export。
 */

// 页面级组件（仅本页面使用）
export * from './ProjectSelectionView';
export * from './ProjectClosureStatusCard';
export * from './ProjectClosureStats';
export * from './ProjectClosureInfo';
export * from './ProjectClosureLessons';
export * from './ProjectClosureQuality';
export * from './ProjectClosureReview';
export * from './ProjectClosureActions';
export * from './ProjectClosureContent';
