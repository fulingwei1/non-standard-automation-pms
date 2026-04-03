import { useRef, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

/**
 * Wraps page content with a CSS fade transition on route changes.
 * Uses pure CSS animations (no heavy libraries).
 * Respects prefers-reduced-motion via CSS media query.
 */
export function AnimatedPage({ children }) {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [animClass, setAnimClass] = useState("page-enter");
  const prevPathRef = useRef(location.pathname);

  useEffect(() => {
    if (location.pathname !== prevPathRef.current) {
      prevPathRef.current = location.pathname;
      // Start exit, then swap content and enter
      setAnimClass("page-exit");
      const timer = setTimeout(() => {
        setDisplayChildren(children);
        setAnimClass("page-enter");
      }, 150); // matches page-fade-out duration
      return () => clearTimeout(timer);
    } else {
      // Same path but children updated (e.g. data change)
      setDisplayChildren(children);
    }
  }, [location.pathname, children]);

  return <div className={animClass}>{displayChildren}</div>;
}
