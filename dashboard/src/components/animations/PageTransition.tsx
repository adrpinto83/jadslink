import React from 'react';

interface PageTransitionProps {
  children: React.ReactNode;
  delay?: number;
}

/**
 * Wrapper component that adds fade-in animation to pages
 */
export const PageTransition: React.FC<PageTransitionProps> = ({ children, delay = 0 }) => {
  return (
    <div
      className="animate-in fade-in duration-500"
      style={{ animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
};

/**
 * Stagger animation for list items
 */
export const StaggerContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="space-y-3">
      {React.Children.map(children, (child, index) => (
        <div
          key={index}
          className="animate-in fade-in slide-in-from-left duration-500"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          {child}
        </div>
      ))}
    </div>
  );
};

/**
 * Bounce animation for emphasis
 */
export const BounceContainer: React.FC<{ children: React.ReactNode; active?: boolean }> = ({
  children,
  active = false,
}) => {
  return (
    <div className={active ? 'animate-bounce' : ''}>
      {children}
    </div>
  );
};
