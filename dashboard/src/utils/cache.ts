/**
 * Centralized caching service for API responses
 * Uses localStorage with TTL support
 */

interface CacheItem {
  data: any;
  timestamp: number;
  ttl: number; // in milliseconds
}

const CACHE_PREFIX = 'jadlink_cache_';

export const cacheService = {
  /**
   * Get cached data if it exists and hasn't expired
   */
  get: (key: string): any | null => {
    try {
      const cached = localStorage.getItem(CACHE_PREFIX + key);
      if (!cached) return null;

      const item: CacheItem = JSON.parse(cached);
      const now = Date.now();

      // Check if cache has expired
      if (now - item.timestamp > item.ttl) {
        cacheService.clear(key);
        return null;
      }

      return item.data;
    } catch {
      return null;
    }
  },

  /**
   * Set cache with TTL (default 1 hour)
   */
  set: (key: string, data: any, ttlMinutes = 60): void => {
    try {
      const item: CacheItem = {
        data,
        timestamp: Date.now(),
        ttl: ttlMinutes * 60 * 1000,
      };
      localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(item));
    } catch (error) {
      console.error('Failed to cache data:', error);
    }
  },

  /**
   * Clear specific cache entry
   */
  clear: (key: string): void => {
    try {
      localStorage.removeItem(CACHE_PREFIX + key);
    } catch {
      // Ignore errors
    }
  },

  /**
   * Clear all cached data
   */
  clearAll: (): void => {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key);
        }
      });
    } catch {
      // Ignore errors
    }
  },
};

/**
 * Hook-style function to get/set cache for async data
 */
export const useCacheWithFallback = async (
  key: string,
  fetchFn: () => Promise<any>,
  ttlMinutes = 60
): Promise<any> => {
  // Try cache first
  const cached = cacheService.get(key);
  if (cached) {
    return cached;
  }

  // Fetch and cache
  try {
    const data = await fetchFn();
    cacheService.set(key, data, ttlMinutes);
    return data;
  } catch (error) {
    console.error(`Failed to fetch ${key}:`, error);
    throw error;
  }
};
