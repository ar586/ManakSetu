const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

// Clean fallback dataset for offline / development mode
const MOCK_STANDARDS = [
  {
    id: "std-456",
    standard_number: "IS 456:2000",
    title: "Plain and Reinforced Concrete - Code of Practice",
    description: "Covers the general structural design and construction guidelines for plain and reinforced concrete structures, specifying material standards, exposure conditions, safety factors, and durability requirements.",
    publication_date: "2000-07-15",
    latest_version: "2000 (Fourth Revision)",
    mandatory_certification: "Mandatory for public & infrastructure works",
    download_link: "https://bis.gov.in/standards/is-456",
    is_active: true
  },
  {
    id: "std-1786",
    standard_number: "IS 1786:2008",
    title: "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
    description: "Specifies requirements for high-yield strength deformed steel bars and wires (TMT bars, Fe 415, Fe 500, Fe 550) used as reinforcement in concrete structures across civil and residential engineering projects.",
    publication_date: "2008-03-20",
    latest_version: "2008 (Fourth Revision)",
    mandatory_certification: "BIS ISI Mark mandatory under QCO 2012",
    download_link: "https://bis.gov.in/standards/is-1786",
    is_active: true
  },
  {
    id: "std-800",
    standard_number: "IS 800:2007",
    title: "General Construction in Steel - Code of Practice",
    description: "Provides comprehensive design criteria for structural steelwork in building construction, covering limit state design methodology, connection details, stability, and fire safety.",
    publication_date: "2007-12-01",
    latest_version: "2007 (Third Revision)",
    mandatory_certification: "BIS Technical Specification Compliant",
    download_link: "https://bis.gov.in/standards/is-800",
    is_active: true
  },
  {
    id: "std-1893",
    standard_number: "IS 1893 (Part 1):2016",
    title: "Criteria for Earthquake Resistant Design of Structures - General Provisions and Buildings",
    description: "Establishes seismic zoning maps, design response spectra, and structural response factors necessary for designing earthquake-resistant residential, commercial, and industrial buildings in India.",
    publication_date: "2016-12-10",
    latest_version: "2016 (Sixth Revision)",
    mandatory_certification: "Mandatory Seismic Zone III, IV & V Compliance",
    download_link: "https://bis.gov.in/standards/is-1893-1",
    is_active: true
  },
  {
    id: "std-10500",
    standard_number: "IS 10500:2012",
    title: "Drinking Water Specification",
    description: "Defines acceptable limits and permissible limits in the absence of an alternate source for physical, chemical, bacteriological, and toxicological parameters of potable water.",
    publication_date: "2012-05-15",
    latest_version: "2012 (Second Revision)",
    mandatory_certification: "Mandatory Quality Control Order for Bottled & Utility Water",
    download_link: "https://bis.gov.in/standards/is-10500",
    is_active: true
  },
  {
    id: "std-1200",
    standard_number: "IS 1200 (Part 1):1992",
    title: "Method of Measurement of Building and Civil Engineering Works - Earthwork",
    description: "Standard methods for measuring quantities of earthwork, excavation, trenching, and backfilling for civil engineering construction contracts and tender preparations.",
    publication_date: "1992-04-10",
    latest_version: "1992 (Fourth Revision)",
    mandatory_certification: "CPWD & Public Works Contract Reference Standard",
    download_link: null,
    is_active: true
  },
  {
    id: "std-875",
    standard_number: "IS 875 (Part 3):2015",
    title: "Design Loads (Other Than Earthquake) For Buildings and Structures - Wind Loads",
    description: "Guidelines for calculating basic wind speeds, terrain category factors, design wind pressures, and structural force coefficients across geographical zones in India.",
    publication_date: "2015-08-30",
    latest_version: "2015 (Third Revision)",
    mandatory_certification: "National Building Code (NBC 2016) Mandatory Reference",
    download_link: "https://bis.gov.in/standards/is-875-3",
    is_active: true
  },
  {
    id: "std-383",
    standard_number: "IS 383:2016",
    title: "Coarse and Fine Aggregate for Concrete - Specification",
    description: "Covers specifications for natural sand, crushed stone sand, and manufactured fine aggregates used in concrete production, grading zones, and maximum allowable silt content.",
    publication_date: "2016-01-20",
    latest_version: "2016 (Third Revision)",
    mandatory_certification: "Concrete Ready-Mix & Pre-cast Quality Compliance",
    download_link: "https://bis.gov.in/standards/is-383",
    is_active: true
  }
];

/**
 * Perform AI semantic search for Indian Standards based on query.
 */
export async function searchStandards({ query, top_k = 5, score_threshold = 0.0 }) {
  const url = `${BASE_URL}${API_PREFIX}/search/`;
  
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
        top_k: top_k,
        score_threshold: score_threshold,
      }),
    });

    if (!res.ok) {
      throw new Error(`Search failed with status ${res.status}`);
    }

    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("API request failed or backend unavailable. Using fallback search engine:", err);
    
    // Fallback search algorithm over dataset
    const q = query.toLowerCase();
    const scored = MOCK_STANDARDS.map((std) => {
      let score = 0.5;
      const text = `${std.standard_number} ${std.title} ${std.description || ""}`.toLowerCase();
      
      if (text.includes(q)) score = 0.96;
      else {
        const words = q.split(/\s+/).filter(w => w.length > 2);
        const matchCount = words.filter(w => text.includes(w)).length;
        if (matchCount > 0) {
          score = Math.min(0.95, 0.6 + (matchCount / words.length) * 0.35);
        }
      }

      return { standard: std, similarity_score: score };
    })
      .filter((item) => item.similarity_score >= score_threshold)
      .sort((a, b) => b.similarity_score - a.similarity_score)
      .slice(0, top_k);

    return {
      query: query,
      results: scored,
    };
  }
}

/**
 * Fetch paginated standards list.
 */
export async function getStandards({ skip = 0, limit = 10 } = {}) {
  const url = `${BASE_URL}${API_PREFIX}/standards/?skip=${skip}&limit=${limit}`;

  try {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch standards: status ${res.status}`);
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("API request failed or backend unavailable. Using fallback standards dataset:", err);
    return MOCK_STANDARDS.slice(skip, skip + limit);
  }
}

/**
 * Fetch single standard by ID.
 */
export async function getStandardById(id) {
  const url = `${BASE_URL}${API_PREFIX}/standards/${encodeURIComponent(id)}`;

  try {
    const res = await fetch(url);
    if (res.status === 404) {
      return null;
    }
    if (!res.ok) {
      throw new Error(`Failed to fetch standard ${id}: status ${res.status}`);
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn(`API request failed for standard ${id}. Searching fallback dataset:`, err);
    const found = MOCK_STANDARDS.find(
      (s) => s.id === id || s.standard_number.toLowerCase() === id.toLowerCase() || encodeURIComponent(s.id) === id
    );
    return found || null;
  }
}
