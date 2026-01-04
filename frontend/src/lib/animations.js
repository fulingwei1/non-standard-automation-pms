/**
 * Framer Motion Animation Presets
 * World-class animations inspired by Stripe, Linear, Vercel
 */

// ============================================
// Basic Transitions
// ============================================

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 },
  // For use with staggerContainer
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
  },
}

export const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const slideDown = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const slideLeft = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const slideRight = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  transition: { type: 'spring', duration: 0.4, bounce: 0.2 },
}

// ============================================
// Page Transitions
// ============================================

export const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const pageVariants = {
  initial: { opacity: 0, y: 20 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -20 },
}

export const pageTransitionConfig = {
  type: 'tween',
  ease: [0.4, 0, 0.2, 1],
  duration: 0.3,
}

// ============================================
// Modal/Dialog Animations
// ============================================

export const modalAnimation = {
  overlay: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  },
  content: {
    initial: { opacity: 0, scale: 0.95, y: 20 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.95, y: 20 },
    transition: { type: 'spring', duration: 0.5, bounce: 0.3 },
  },
}

export const sheetAnimation = {
  overlay: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  },
  content: {
    initial: { y: '100%' },
    animate: { y: 0 },
    exit: { y: '100%' },
    transition: { type: 'spring', damping: 30, stiffness: 300 },
  },
}

export const dropdownAnimation = {
  initial: { opacity: 0, scale: 0.95, y: -5 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: -5 },
  transition: { duration: 0.15, ease: [0.4, 0, 0.2, 1] },
}

// ============================================
// List Item Animations
// ============================================

export const listItem = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: { type: 'spring', stiffness: 300, damping: 30 },
}

export const listItemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

// Stagger Container - Use with children
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
}

export const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
}

// ============================================
// Hover/Tap Effects
// ============================================

export const hoverScale = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 },
  transition: { type: 'spring', stiffness: 400, damping: 25 },
}

export const hoverLift = {
  whileHover: { y: -4 },
  transition: { type: 'spring', stiffness: 300, damping: 20 },
}

export const hoverGlow = {
  whileHover: {
    boxShadow: '0 0 25px -5px rgba(139, 92, 246, 0.4)',
  },
  transition: { duration: 0.3 },
}

export const buttonTap = {
  whileTap: { scale: 0.97 },
  transition: { type: 'spring', stiffness: 500, damping: 30 },
}

export const cardHover = {
  whileHover: { y: -4, scale: 1.01 },
  whileTap: { scale: 0.99 },
  transition: { type: 'spring', stiffness: 400, damping: 25 },
}

// ============================================
// Notification Animations
// ============================================

export const toastAnimation = {
  initial: { opacity: 0, y: 50, scale: 0.95 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: 20, scale: 0.95 },
  transition: { type: 'spring', stiffness: 400, damping: 30 },
}

export const shake = {
  x: [0, -10, 10, -10, 10, 0],
  transition: { duration: 0.5 },
}

export const pulse = {
  scale: [1, 1.05, 1],
  transition: { repeat: Infinity, duration: 2 },
}

// ============================================
// Navigation Animations
// ============================================

export const navItemAnimation = {
  rest: { scale: 1 },
  hover: { scale: 1.02 },
  pressed: { scale: 0.98 },
}

export const activeIndicator = {
  layoutId: 'activeNav',
  transition: { type: 'spring', duration: 0.5 },
}

// ============================================
// Sidebar Animations
// ============================================

export const sidebarAnimation = {
  expanded: { width: 240 },
  collapsed: { width: 72 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
}

export const sidebarTextAnimation = {
  expanded: { opacity: 1, width: 'auto' },
  collapsed: { opacity: 0, width: 0 },
  transition: { duration: 0.2 },
}

// ============================================
// Loading Animations
// ============================================

export const skeletonAnimation = {
  backgroundPosition: ['-200% 0', '200% 0'],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'linear',
  },
}

export const spinnerAnimation = {
  rotate: 360,
  transition: {
    duration: 1,
    repeat: Infinity,
    ease: 'linear',
  },
}

export const pulseAnimation = {
  opacity: [0.5, 1, 0.5],
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: 'easeInOut',
  },
}

// ============================================
// Spring Configs
// ============================================

export const springConfig = {
  gentle: { type: 'spring', stiffness: 120, damping: 14 },
  wobbly: { type: 'spring', stiffness: 180, damping: 12 },
  stiff: { type: 'spring', stiffness: 300, damping: 30 },
  slow: { type: 'spring', stiffness: 100, damping: 20 },
  molasses: { type: 'spring', stiffness: 60, damping: 20 },
}

// ============================================
// Utility function to create variants
// ============================================

export function createVariants(initial, animate, exit = initial) {
  return {
    initial,
    animate,
    exit,
  }
}

// ============================================
// Stagger helper
// ============================================

export function createStaggerVariants(delayPerChild = 0.05) {
  return {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: delayPerChild,
        },
      },
    },
    item: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    },
  }
}

