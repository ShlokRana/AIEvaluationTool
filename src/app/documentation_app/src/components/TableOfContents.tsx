import React from 'react';
import { cn } from '../lib/utils';
import { Heading } from '../App';

interface TableOfContentsProps {
  headings: Heading[];
  activeHeadingId: string | null;
}

export function TableOfContents({ headings, activeHeadingId }: TableOfContentsProps) {
  if (headings.length === 0) return null;

  const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="hidden w-72 shrink-0 self-start xl:block">
      <div className="sticky top-16 h-[calc(100vh-4rem)] px-6 py-12 2xl:px-8">
        <div className="flex h-full min-h-0 flex-col">
          <h4 className="mb-6 text-xs font-bold uppercase tracking-widest text-foreground/40">
            On this page
          </h4>
          <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto border-l border-border pr-1 pb-10 scrollbar-hide">
            {headings.map((heading) => {
              const isActive = activeHeadingId === heading.id;
              return (
                <button
                  key={heading.id}
                  onClick={() => scrollToHeading(heading.id)}
                  className={cn(
                    "w-full text-left px-4 py-1.5 text-xs transition-all border-l-2 -ml-[1px]",
                    heading.level === 3 ? "pl-8" : "pl-4",
                    isActive
                      ? "text-primary font-semibold border-primary bg-primary/5"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent border-transparent"
                  )}
                >
                  {heading.text}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}
