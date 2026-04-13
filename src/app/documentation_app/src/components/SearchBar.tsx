import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Search, FileText, Hash, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { DocId, DOCS_CONFIG } from '../constants/docs';
import { Heading } from '../App';
import { cn } from '../lib/utils';

interface SearchResult {
  docId: DocId;
  heading?: Heading;
  type: 'doc' | 'heading';
  text: string;
  docTitle: string;
  score: number;
}

interface SearchBarProps {
  allHeadings: Record<DocId, Heading[]>;
  onSelect: (docId: DocId, headingId?: string) => void;
  autoFocus?: boolean;
}

export function SearchBar({ allHeadings, onSelect, autoFocus }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const searchableItems = useMemo(() => {
    return Object.entries(DOCS_CONFIG).flatMap(([id, config]) => {
      const docId = id as DocId;
      const docTitle = config.title;
      const headings = allHeadings[docId] || [];

      const docEntry: Omit<SearchResult, 'score'> = {
        docId,
        type: 'doc',
        text: docTitle,
        docTitle,
      };

      const headingEntries = headings.map((heading) => ({
        docId,
        heading,
        type: 'heading' as const,
        text: heading.text,
        docTitle,
      }));

      return [docEntry, ...headingEntries];
    });
  }, [allHeadings]);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const results = useMemo(() => {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) return [];

    return searchableItems
      .map((item) => ({
        ...item,
        score: getSearchScore(item.text, normalizedQuery, item.type),
      }))
      .filter((item) => item.score > 0)
      .sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        if (a.type !== b.type) return a.type === 'doc' ? -1 : 1;
        return a.text.localeCompare(b.text);
      })
      .slice(0, 8);
  }, [query, searchableItems]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [results]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const activeResult = resultRefs.current[selectedIndex];
    if (activeResult) {
      activeResult.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  const selectResult = (result: SearchResult) => {
    onSelect(result.docId, result.heading?.id);
    setIsOpen(false);
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!results.length && e.key !== 'Escape') return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % results.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      e.preventDefault();
      selectResult(results[selectedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const showDropdown = isOpen && query.trim().length > 0;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="relative group">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search documentation..."
          role="combobox"
          aria-expanded={showDropdown}
          aria-controls="docs-search-results"
          aria-activedescendant={results[selectedIndex] ? `search-result-${selectedIndex}` : undefined}
          className="w-full rounded-lg border border-border bg-card py-2.5 pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-zinc-500/20 focus:border-zinc-400 dark:focus:border-zinc-500 transition-all"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('');
              setSelectedIndex(0);
              inputRef.current?.focus();
            }}
            aria-label="Clear search"
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-0.5 transition-colors hover:bg-accent"
          >
            <X className="w-3 h-3 text-muted-foreground" />
          </button>
        )}
      </div>

      <AnimatePresence>
        {showDropdown && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="absolute top-full left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-border bg-popover shadow-2xl"
          >
            <div id="docs-search-results" role="listbox" className="max-h-[400px] overflow-y-auto p-2 space-y-1">
              {results.length > 0 ? results.map((result, index) => (
                <button
                  key={`${result.docId}-${result.heading?.id || 'main'}`}
                  id={`search-result-${index}`}
                  ref={(node) => {
                    resultRefs.current[index] = node;
                  }}
                  onClick={() => selectResult(result)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all text-left",
                    index === selectedIndex
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent/60"
                  )}
                >
                  {result.type === 'doc' ? (
                    <FileText className={cn("w-4 h-4 shrink-0", index === selectedIndex ? "text-accent-foreground" : "text-muted-foreground")} />
                  ) : (
                    <Hash className={cn("w-4 h-4 shrink-0", index === selectedIndex ? "text-accent-foreground" : "text-muted-foreground")} />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{result.text}</div>
                    <div className="text-[11px] text-muted-foreground truncate">
                      {result.type === 'doc' ? 'Document' : `In ${result.docTitle}`}
                    </div>
                  </div>
                </button>
              )) : (
                <div className="px-3 py-4 text-sm text-muted-foreground">
                  No results found for <span className="font-medium text-foreground">"{query.trim()}"</span>.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function normalizeSearchText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^\w\s-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getSearchScore(text: string, query: string, type: SearchResult['type']) {
  const normalizedText = normalizeSearchText(text);
  if (!normalizedText) return 0;
  if (normalizedText === query) return type === 'doc' ? 120 : 110;
  if (normalizedText.startsWith(query)) return type === 'doc' ? 95 : 88;

  const words = normalizedText.split(' ');
  const queryWords = query.split(' ');
  const matchedWords = queryWords.filter((word) =>
    words.some((textWord) => textWord.startsWith(word) || textWord.includes(word))
  );

  if (matchedWords.length === queryWords.length) {
    return (type === 'doc' ? 80 : 72) + matchedWords.length * 4;
  }

  if (normalizedText.includes(query)) {
    return type === 'doc' ? 60 : 54;
  }

  return 0;
}
