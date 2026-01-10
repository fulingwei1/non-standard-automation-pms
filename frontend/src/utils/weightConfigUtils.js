/**
 * 权重配置工具函数
 */

/**
 * 默认权重配置
 */
export const defaultWeights = {
  deptManager: 50,
  projectManager: 50
}

/**
 * 动画配置
 */
export const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 }
}

/**
 * 验证权重总和
 */
export const validateWeights = (weights) => {
  const totalWeight = weights.deptManager + weights.projectManager
  return {
    totalWeight,
    isValid: totalWeight === 100
  }
}
