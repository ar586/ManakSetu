"use client";

import { useState } from "react";
import HeroSearch from "@/components/HeroSearch";
import SearchResults from "@/components/SearchResults";
import HowItWorks from "@/components/HowItWorks";
import FeaturedStandards from "@/components/FeaturedStandards";
import CTASection from "@/components/CTASection";
import { searchStandards } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [searchData, setSearchData] = useState(null);

  const handleSearch = async (searchQuery) => {
    setQuery(searchQuery);
    setSearching(true);
    setSearchError(false);

    // Scroll smoothly to results section
    setTimeout(() => {
      const el = document.getElementById("results");
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    }, 100);

    try {
      const data = await searchStandards({ query: searchQuery, top_k: 5 });
      setSearchData(data);
    } catch (err) {
      console.error("Search failed:", err);
      setSearchError(true);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-12">
      {/* Hero & Search Interface */}
      <HeroSearch onSearch={handleSearch} isSearching={searching} />

      {/* Dynamic Search Results */}
      <SearchResults
        query={query}
        loading={searching}
        error={searchError}
        data={searchData}
        onRetry={() => handleSearch(query)}
      />

      {/* Editorial How It Works Section */}
      <HowItWorks />

      {/* Featured Catalog Preview */}
      <FeaturedStandards />

      {/* Primary Final Call to Action */}
      <CTASection />
    </div>
  );
}
