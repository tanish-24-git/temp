/**
 * Chunk Location Parser Utilities
 * 
 * Helper functions to parse and format chunk locations from violation records.
 * Handles format: chunk:{uuid}:page:{num}:offset:{start}
 */

export interface ParsedChunkLocation {
    isChunkBased: boolean;
    chunkId?: string;
    pageNumber?: number;
    charOffset?: number;
    rawLocation: string;
}

/**
 * Parse chunk location string from violation.location
 * 
 * @param location - Location string from violation (e.g., "chunk:uuid-here:page:3:offset:1500")
 * @returns Parsed location object
 */
export function parseChunkLocation(location: string): ParsedChunkLocation {
    if (!location) {
        return {
            isChunkBased: false,
            rawLocation: location || ''
        };
    }

    // Check if location follows chunk format
    if (!location.startsWith('chunk:')) {
        return {
            isChunkBased: false,
            rawLocation: location
        };
    }

    const result: ParsedChunkLocation = {
        isChunkBased: true,
        rawLocation: location
    };

    // Parse chunk ID
    const parts = location.split(':');
    if (parts.length >= 2) {
        result.chunkId = parts[1];
    }

    // Parse page number (if present)
    const pageIndex = parts.indexOf('page');
    if (pageIndex !== -1 && parts.length > pageIndex + 1) {
        const pageNum = parseInt(parts[pageIndex + 1], 10);
        if (!isNaN(pageNum)) {
            result.pageNumber = pageNum;
        }
    }

    // Parse character offset (if present)
    const offsetIndex = parts.indexOf('offset');
    if (offsetIndex !== -1 && parts.length > offsetIndex + 1) {
        const offset = parseInt(parts[offsetIndex + 1], 10);
        if (!isNaN(offset)) {
            result.charOffset = offset;
        }
    }

    return result;
}

/**
 * Format chunk metadata as human-readable location string
 * 
 * @param metadata - Chunk metadata from ContentChunk
 * @returns Human-readable location string (e.g., "Page 3, Characters 1500-2000")
 */
export function formatChunkLocation(metadata: any): string {
    const parts: string[] = [];

    if (metadata?.page_number) {
        parts.push(`Page ${metadata.page_number}`);
    }

    if (metadata?.section_title) {
        parts.push(`Section: ${metadata.section_title}`);
    }

    if (metadata?.char_offset_start !== undefined) {
        const start = metadata.char_offset_start;
        const end = metadata.char_offset_end || start;
        parts.push(`Characters ${start}-${end}`);
    }

    if (parts.length === 0 && metadata?.chunk_index !== undefined) {
        parts.push(`Chunk ${metadata.chunk_index + 1}`);
    }

    return parts.join(', ') || 'Unknown location';
}

/**
 * Extract chunk ID from location string
 * 
 * @param location - Location string
 * @returns Chunk ID or null
 */
export function extractChunkId(location: string): string | null {
    const parsed = parseChunkLocation(location);
    return parsed.chunkId || null;
}

/**
 * Check if location is chunk-based
 * 
 * @param location - Location string
 * @returns True if location follows chunk format
 */
export function isChunkBasedLocation(location: string): boolean {
    return parseChunkLocation(location).isChunkBased;
}
