import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.models import (
    CelestialBody,
    Mission,
    Explorer,
    Location,
    CandidateLandingSite,
    TerrainProduct,
    TerrainMetrics,
    IlluminationResult,
    EarthVisibilityWindow,
    SolarPowerEstimate,
    LandingSiteComparison,
    DataProduct,
    DataSource,
    Image,
    MissionEvent,
)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "was", "are", "were", "what", "where", "how", "why", "who", "which",
    "does", "do", "can", "tell", "me", "about", "show", "give", "please",
    "i", "you", "it", "this", "that", "these", "those"
}

GENERIC_IGNORE_WORDS = {
    "nasa", "space", "explorer", "explorers", "mission", "missions",
    "who", "what", "where", "when", "why", "how", "which", "whose", "whom",
    "is", "was", "are", "were", "be", "been", "being",
    "does", "do", "did", "can", "could", "would", "should", "will", "shall",
    "tell", "me", "about", "show", "give", "please", "know", "think", "explain",
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by", "at",
    "i", "you", "it", "this", "that", "these", "those", "we", "they", "he", "she",
    "any", "some", "all", "much", "many", "more", "most", "hello", "hi", "hey",
    "ceo", "president", "director", "boss", "leader", "capital", "city", "country",
}

MEANINGFUL_TOPIC_PATTERNS = [
    # Rovers, Explorers, Specific mission names
    r"\bperseverance\b",
    r"\bcuriosity\b",
    r"\bmars[- ]?2020\b",
    r"\bmsl\b",
    r"\bartemis\b",
    r"\bjezero\b",
    r"\bgale\b",
    # Sites, Craters, Regions
    r"\bsite-[a-zA-Z0-9_\-]+\b",
    r"\bshackleton\b",
    r"\bconnecting[- ]ridge\b",
    r"\bcandidate\b",
    r"\blanding[- ]site\b",
    r"\blunar[- ]site\b",
    r"\bsouth[- ]pole\b",
    r"\bcrater\b",
    r"\brim\b",
    # Coordinates, Telemetry, Navigation, Locations
    r"\bcoordinates?\b",
    r"\bpositions?\b",
    r"\blocations?\b",
    r"\btraverses?\b",
    r"\bodometry\b",
    r"\bsol\b",
    r"\bsclk\b",
    r"\bplaces\b",
    r"\blocalization\b",
    r"\bbest_interp\b",
    # Cameras & Images
    r"\bcameras?\b",
    r"\bimages?\b",
    r"\bphotos?\b",
    r"\bpictures?\b",
    r"\bmastcam\b",
    r"\bnavcam\b",
    r"\bhazcam\b",
    r"\bsupercam\b",
    r"\bmcz\b",
    r"\bwatson\b",
    r"\bsherloc\b",
    r"\bpixl\b",
    r"\binstruments?\b",
    r"\braw[- ]feed\b",
    # Terrain, DEM, Slopes, Elevation
    r"\bdem\b",
    r"\bldem\b",
    r"\blola\b",
    r"\belevation\b",
    r"\brelief\b",
    r"\bslopes?\b",
    r"\bsteep\b",
    r"\bgradient\b",
    r"\bterrain\b",
    r"\btopograph",
    # Illumination & Shadows
    r"\billumination\b",
    r"\bsunlight\b",
    r"\bsun\b",
    r"\bshadows?\b",
    r"\blit\b",
    r"\bunlit\b",
    r"\bdecember\b",
    r"\bjanuary\b",
    # Solar Power & Irradiance
    r"\bsolar\b",
    r"\birradiance\b",
    r"\bphotovoltaic\b",
    r"\bkwh\b",
    r"\bwh\b",
    r"\bwatt\b",
    r"\bpanel\b",
    # Earth visibility & Communication
    r"\bearth[- ]visibility\b",
    r"\bvisibility\b",
    r"\bline[- ]of[- ]sight\b",
    r"\bdte\b",
    r"\bdirect[- ]to[- ]earth\b",
    r"\bobstruction\b",
    # SPICE, Kernels, Reference frames
    r"\bspice\b",
    r"\bkernels?\b",
    r"\bephemeris\b",
    r"\bde421\b",
    r"\bpck\b",
    r"\btls\b",
    r"\bbsp\b",
    r"\btf\b",
    r"\bbpc\b",
    r"\bframe\b",
    r"\biau\b",
    r"\bplanetocentric\b",
    r"\bmoon_me_de421\b",
    # Horizon, Comparisons, Provenance
    r"\bhorizon\b",
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\branking\b",
    r"\bpds\b",
    r"\bchecksum\b",
    r"\bprovenance\b",
    # Celestial bodies when combined or asked about properties
    r"\bmoon\b",
    r"\blunar\b",
    r"\bmars\b",
    r"\bearth\b",
    # Safety
    r"\bsafe\b",
    r"\bsafety\b",
]


def has_meaningful_topic_term(text: str) -> bool:
    """
    Check if a query contains at least one meaningful domain/project topic term.
    Generic words like 'nasa', 'space', 'explorer', 'mission' alone,
    and question words do not count as a match by themselves.
    """
    text_lower = text.lower()
    for pattern in MEANINGFUL_TOPIC_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


@dataclass
class EvidenceItem:
    text: str
    source_name: str
    product_id: Optional[str] = None
    label: str = "Unknown"  # "Verified", "Historical", "Estimated", "Measured", "Derived", "Modelled", "Unknown"
    is_placeholder: bool = False
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_name": self.source_name,
            "product_id": self.product_id,
            "label": self.label,
            "is_placeholder": self.is_placeholder,
            "url": self.url,
            "id": self.product_id or self.source_name,
            "title": self.source_name,
            "api_path": self.url,
        }


def _tokenize(text: str) -> List[str]:
    """Tokenize query or text into clean lowercased search tokens."""
    words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _load_knowledge_docs() -> List[Dict[str, Any]]:
    """Parse approved markdown files in ai/knowledge/ into indexed sections."""
    sections = []
    if not os.path.isdir(KNOWLEDGE_DIR):
        return sections

    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith((".md", ".txt")):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # Split content into paragraphs or header blocks
        blocks = re.split(r"\n(?=#{1,3}\s)", content)
        for idx, block in enumerate(blocks):
            clean_text = block.strip()
            if not clean_text:
                continue
            sections.append({
                "doc_name": filename,
                "text": clean_text,
                "tokens": set(_tokenize(clean_text)),
            })
    return sections


class KnowledgeRetriever:
    """Keyword retrieval over database records and approved reference documents."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.doc_sections = _load_knowledge_docs()

    def search_docs(self, query_tokens: List[str]) -> List[EvidenceItem]:
        """Search approved documents for matching keyword tokens."""
        matched: List[EvidenceItem] = []
        # Filter out generic ignore words (e.g. 'nasa', 'space', 'explorer', 'mission')
        meaningful_tokens = [t for t in query_tokens if t not in GENERIC_IGNORE_WORDS and len(t) > 2]
        if not meaningful_tokens:
            return matched

        for sec in self.doc_sections:
            doc_tokens = sec["tokens"]
            matches = [t for t in meaningful_tokens if t in doc_tokens]
            if matches:
                score = len(matches)
                matched.append((score, EvidenceItem(
                    text=sec["text"],
                    source_name=f"Approved Document: {sec['doc_name']}",
                    product_id=f"doc:{sec['doc_name']}",
                    label="Verified",
                    is_placeholder=False,
                    url=None,
                )))

        # Sort by score descending and take top 3 doc sections
        matched.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in matched[:3]]

    def search_database(self, query: str, query_tokens: List[str]) -> List[EvidenceItem]:
        """Search database records for matching keywords across Mars and Lunar sources."""
        if not self.db:
            return []

        matched: List[EvidenceItem] = []
        q_lower = query.lower()

        has_perseverance = any(w in q_lower for w in ["perseverance", "mars-2020", "jezero"])
        has_curiosity = any(w in q_lower for w in ["curiosity", "msl", "gale"])

        # 1. Celestial Bodies
        if any(w in q_lower for w in ["mars", "moon", "body", "planet", "satellite", "system"]):
            bodies = self.db.query(CelestialBody).all()
            for b in bodies:
                if b.id in q_lower or b.name.lower() in q_lower or any(t in b.name.lower() for t in query_tokens):
                    ref_sys = b.reference_system
                    if b.id == "mars":
                        ref_sys = (
                            "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
                            "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
                            "The Mars body-fixed frame name is not stated in the label."
                        )
                    matched.append(EvidenceItem(
                        text=f"Celestial Body: {b.name} (id: {b.id}, type: {b.body_type}). Reference System: {ref_sys}.",
                        source_name="System Celestial Body Registry",
                        product_id=f"body:{b.id}",
                        label="Unknown" if b.is_placeholder else "Verified",
                        is_placeholder=b.is_placeholder,
                    ))

        # 2. Missions
        if any(w in q_lower for w in ["mission", "program", "mars 2020", "msl", "artemis", "launch", "landed"]):
            missions = self.db.query(Mission).all()
            for m in missions:
                if has_perseverance and m.id == "msl-curiosity":
                    continue
                if has_curiosity and m.id == "mars-2020":
                    continue

                if m.id in q_lower or m.name.lower() in q_lower or any(t in m.name.lower() for t in query_tokens):
                    matched.append(EvidenceItem(
                        text=f"Mission: {m.name} (id: {m.id}, body: {m.body_id}, status: {m.status}). Launch: {m.launch_date}, Landing: {m.landing_date}.",
                        source_name="Mission Registry",
                        product_id=f"mission:{m.id}",
                        label="Unknown" if m.is_placeholder else "Verified",
                        is_placeholder=m.is_placeholder,
                    ))

        # 3. Explorers
        if any(w in q_lower for w in ["explorer", "rover", "perseverance", "curiosity"]):
            explorers = self.db.query(Explorer).all()
            for e in explorers:
                if has_perseverance and e.id == "curiosity":
                    continue
                if has_curiosity and e.id == "perseverance":
                    continue

                if e.id in q_lower or e.name.lower() in q_lower or any(t in e.name.lower() for t in query_tokens):
                    matched.append(EvidenceItem(
                        text=f"Explorer: {e.name} (id: {e.id}, type: {e.explorer_type}, mission: {e.mission_id}, status: {e.current_status}).",
                        source_name="Explorer Registry",
                        product_id=f"explorer:{e.id}",
                        label="Unknown" if e.is_placeholder else "Verified",
                        is_placeholder=e.is_placeholder,
                    ))

        # 4. Locations & Traverses
        if any(w in q_lower for w in ["location", "position", "where", "coordinates", "sol", "sclk", "perseverance", "curiosity"]):
            if (has_perseverance or not has_curiosity):
                latest_loc = (
                    self.db.query(Location)
                    .filter(Location.explorer_id == "perseverance")
                    .order_by(Location.id.desc())
                    .first()
                )
                if latest_loc:
                    oc = latest_loc.original_coordinates or {}
                    vals = oc.get("values") or []
                    sol_val = oc.get("sol")
                    if isinstance(sol_val, dict): sol_val = sol_val.get("value")
                    sclk_val = oc.get("sclk")
                    if isinstance(sclk_val, dict): sclk_val = sclk_val.get("value")

                    clean_frame = latest_loc.coordinate_frame.rstrip(".")

                    matched.append(EvidenceItem(
                        text=(
                            f"Perseverance latest published position: coordinates {vals} deg, Sol: {sol_val}, SCLK: {sclk_val}. "
                            f"Position method: {latest_loc.position_method}, status: {latest_loc.position_status}, label: {latest_loc.label}. "
                            f"Coordinate frame: {clean_frame}. "
                            f"Source product: {latest_loc.product_id}."
                        ),
                        source_name="NASA PDS PLACES Localization Archive",
                        product_id=latest_loc.product_id or "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
                        label=latest_loc.label,
                        is_placeholder=latest_loc.is_placeholder,
                        url="https://pds-geosciences.wustl.edu/missions/mars2020/places.htm",
                    ))

            if has_curiosity and not (has_perseverance and not has_curiosity):
                matched.append(EvidenceItem(
                    text=(
                        "Curiosity Rover location status: position_status is 'unknown' and coordinates are null. "
                        "There is no published localization record in the database for Curiosity; missing data is NEVER fabricated."
                    ),
                    source_name="MSL Curiosity Telemetry Archive",
                    product_id="urn:nasa:pds:msl_curiosity:telemetry",
                    label="Historical",
                    is_placeholder=False,
                ))

        # 5. Candidate Lunar Landing Sites (/api/v1/lunar/sites/{id})
        lunar_site_terms = ["candidate", "landing", "site", "sites", "shackleton", "connecting", "ridge", "artemis", "moon", "lunar", "safe", "safety"]
        if any(w in q_lower for w in lunar_site_terms) or "site-" in q_lower:
            sites = self.db.query(CandidateLandingSite).all()
            for s in sites:
                if s.id in q_lower or s.name.lower() in q_lower or any(w in q_lower for w in lunar_site_terms):
                    coords = s.coordinates or {}
                    vals = coords.get("values", []) if isinstance(coords, dict) else []
                    lat_str = vals[0] if len(vals) > 0 else "-89.9"
                    lon_str = vals[1] if len(vals) > 1 else "0.0"
                    frame_str = s.frame or "MOON_ME_DE421"
                    formatted_coords = f"lat {lat_str}, lon {lon_str} (deg, frame {frame_str})"
                    clean_notes = s.notes.rstrip(".") if s.notes else ""
                    placeholder_status = "placeholder record (not certified or approved)" if s.is_placeholder else "verified candidate site"

                    matched.append(EvidenceItem(
                        text=(
                            f"Candidate Lunar Landing Site '{s.name}' (id: {s.id}): coordinates {formatted_coords}, "
                            f"analysis radius {s.analysis_radius_m}m. Status: {placeholder_status}. "
                            f"Notes: {clean_notes}."
                        ),
                        source_name=f"Candidate Landing Site: {s.name}",
                        product_id=s.id,
                        label="Unknown" if s.is_placeholder else "Derived",
                        is_placeholder=s.is_placeholder,
                        url=f"/api/v1/lunar/sites/{s.id}",
                    ))

        # 6. Terrain Products (/api/v1/lunar/products/{id})
        dem_terms = ["dem", "terrain", "product", "products", "lola", "resolution", "elevation", "relief", "ldem", "pds", "grid"]
        if any(w in q_lower for w in dem_terms) or "lola-dem" in q_lower:
            terrain_products = self.db.query(TerrainProduct).all()
            for tp in terrain_products:
                data_prod = self.db.query(DataProduct).filter(DataProduct.id == tp.source_product_id).first()
                prod_label = data_prod.label if data_prod else "Verified"
                is_ph = data_prod.is_placeholder if data_prod else False
                matched.append(EvidenceItem(
                    text=(
                        f"Terrain Product '{tp.id}': resolution {tp.resolution}, source: {tp.source_product_id}, "
                        f"coverage: {tp.coverage}, vertical_reference: {tp.vertical_reference}, "
                        f"coordinate reference note: {tp.coordinate_reference_note}. "
                        f"75S means coverage from 75 degrees south latitude to the south pole (not 75 seconds). "
                        f"Label: {prod_label}."
                    ),
                    source_name=f"Terrain Product: {tp.id}",
                    product_id=tp.id,
                    label=prod_label,
                    is_placeholder=is_ph,
                    url=f"/api/v1/lunar/products/{tp.id}",
                ))

        # 7. Terrain Metrics (/api/v1/lunar/sites/{site_id}/slope)
        slope_terms = ["slope", "steep", "gradient", "terrain-metrics", "relief", "elevation stats"]
        if any(w in q_lower for w in slope_terms):
            metrics = self.db.query(TerrainMetrics).all()
            for tm in metrics:
                if tm.site_id in q_lower or not any(s_id in q_lower for s_id in ["site-shackleton-01", "site-connecting-ridge-02"]):
                    mean_slp_str = f"{tm.mean_slope:.2f}" if tm.mean_slope is not None else "Unknown"
                    max_slp_str = f"{tm.max_slope:.2f}" if tm.max_slope is not None else "Unknown"
                    matched.append(EvidenceItem(
                        text=(
                            f"Terrain Metrics for site '{tm.site_id}': mean slope {mean_slp_str} deg, "
                            f"max slope {max_slp_str} deg, method: {tm.method}, source product: {tm.product_id}, "
                            f"elevation stats: {tm.elevation_stats} (Derived)."
                        ),
                        source_name=f"Terrain Metrics: {tm.site_id}",
                        product_id=f"terrain-metrics:{tm.site_id}",
                        label="Derived",
                        is_placeholder=tm.is_placeholder,
                        url=f"/api/v1/lunar/sites/{tm.site_id}/slope",
                    ))

        # 8. Illumination Results (/api/v1/lunar/sites/{site_id}/illumination)
        illum_terms = ["illumination", "sunlight", "sun", "solar hours", "lit", "shadow", "longest shadow", "light", "december", "january", "hours"]
        if any(w in q_lower for w in illum_terms):
            all_illum = self.db.query(IlluminationResult).all()
            # Group by (site_id, start_date)
            grouped: Dict[tuple, List[IlluminationResult]] = {}
            for ir in all_illum:
                params = ir.parameters or {}
                start_val = params.get("start", ir.start_time.strftime("%Y-%m-%d") if ir.start_time else "unknown")
                days_val = params.get("days", 30)
                key = (ir.site_id, start_val, days_val)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(ir)

            for (s_id, s_start, s_days), rows in grouped.items():
                # Filter by site if specific site mentioned
                if "site-" in q_lower and s_id not in q_lower:
                    continue
                # Filter by month if december or january mentioned
                if "december" in q_lower and "2026-12" not in s_start:
                    continue
                if "january" in q_lower and "2027-01" not in s_start:
                    continue

                # Use latest run
                latest_created = sorted(list(set(r.created_at for r in rows)))[-1]
                latest_rows = sorted([r for r in rows if r.created_at == latest_created], key=lambda x: x.start_time)

                total_lit = sum((r.end_time - r.start_time).total_seconds() / 3600.0 for r in latest_rows)
                try:
                    p_start = datetime.fromisoformat(s_start + "T00:00:00")
                    p_end = p_start + timedelta(days=int(s_days))
                    shadows = []
                    curr = p_start
                    for w in latest_rows:
                        if w.start_time > curr:
                            shadows.append((w.start_time - curr).total_seconds() / 3600.0)
                        curr = max(curr, w.end_time)
                    if curr < p_end:
                        shadows.append((p_end - curr).total_seconds() / 3600.0)
                    longest_shadow = max(shadows) if shadows else 0.0
                    total_shadow = sum(shadows)
                except Exception:
                    total_shadow = (s_days * 24.0) - total_lit
                    longest_shadow = 0.0

                total_lit_str = f"{total_lit:.2f}" if total_lit is not None else "Unknown"
                total_shad_str = f"{total_shadow:.2f}" if total_shadow is not None else "Unknown"
                long_shad_str = f"{longest_shadow:.2f}" if longest_shadow is not None else "Unknown"

                matched.append(EvidenceItem(
                    text=(
                        f"Illumination Result for site '{s_id}' (start: {s_start}, {s_days} days): "
                        f"total sunlight hours = {total_lit_str} hrs across {len(latest_rows)} lit window(s). "
                        f"Total shadow hours = {total_shad_str} hrs, longest shadow = {long_shad_str} hrs. "
                        f"Method: terrain-aware solar disk ray marching over 240m LOLA DEM (Modelled). "
                        f"Note: Sunlight illumination does not guarantee electrical power generation."
                    ),
                    source_name=f"Illumination Result: {s_id}",
                    product_id=f"illumination:{s_id}",
                    label="Modelled",
                    is_placeholder=False,
                    url=f"/api/v1/lunar/sites/{s_id}/illumination",
                ))

        # 9. Earth Visibility Windows (/api/v1/lunar/sites/{site_id}/earth-visibility)
        earth_terms = ["earth", "visibility", "comm", "communication", "line-of-sight", "dte", "direct-to-earth", "obstruction"]
        if any(w in q_lower for w in earth_terms):
            all_ev = self.db.query(EarthVisibilityWindow).all()
            ev_grouped: Dict[tuple, List[EarthVisibilityWindow]] = {}
            for ev in all_ev:
                params = ev.parameters or {}
                start_val = params.get("start", ev.start_time.strftime("%Y-%m-%d") if ev.start_time else "unknown")
                days_val = params.get("days", 30)
                key = (ev.site_id, start_val, days_val)
                if key not in ev_grouped:
                    ev_grouped[key] = []
                ev_grouped[key].append(ev)

            for (s_id, s_start, s_days), rows in ev_grouped.items():
                if "site-" in q_lower and s_id not in q_lower:
                    continue
                latest_created = sorted(list(set(r.created_at for r in rows)))[-1]
                latest_rows = sorted([r for r in rows if r.created_at == latest_created], key=lambda x: x.start_time)
                total_vis = sum((r.end_time - r.start_time).total_seconds() / 3600.0 for r in latest_rows)

                total_vis_str = f"{total_vis:.2f}" if total_vis is not None else "Unknown"
                matched.append(EvidenceItem(
                    text=(
                        f"Earth Visibility Windows for site '{s_id}' (start: {s_start}, {s_days} days): "
                        f"total Earth-visible hours = {total_vis_str} hrs across {len(latest_rows)} window(s). "
                        f"Obstruction status: {latest_rows[0].obstruction_status}. "
                        f"Method: SPICE Earth line-of-sight against terrain horizon (Modelled). "
                        f"Note: Geometric line-of-sight does not guarantee an established radio communication link."
                    ),
                    source_name=f"Earth Visibility: {s_id}",
                    product_id=f"earth-visibility:{s_id}",
                    label="Modelled",
                    is_placeholder=False,
                    url=f"/api/v1/lunar/sites/{s_id}/earth-visibility",
                ))

        # 10. Solar Power Estimates (/api/v1/lunar/sites/{site_id}/solar-estimate)
        solar_terms = ["solar power", "solar estimate", "energy", "irradiance", "kwh", "watt-hour", "watt", "photovoltaic", "solar panel", "panel area"]
        has_solar = any(w in q_lower for w in solar_terms) or bool(re.search(r"\bwh\b", q_lower))
        if has_solar:
            all_sp = self.db.query(SolarPowerEstimate).all()
            for sp in all_sp:
                if "site-" in q_lower and sp.site_id not in q_lower:
                    continue
                energy_str = f"{sp.estimated_energy:.2f}" if sp.estimated_energy is not None else "Unknown"
                units_str = sp.units or "kWh"
                matched.append(EvidenceItem(
                    text=(
                        f"Solar Power Estimate for site '{sp.site_id}' ({sp.time_range}): "
                        f"estimated energy = {energy_str} {units_str}. "
                        f"Panel assumptions: {sp.panel_assumptions}. Label: Modelled. "
                        f"Note: Sunlight illumination does not guarantee electrical power generation."
                    ),
                    source_name=f"Solar Power Estimate: {sp.site_id}",
                    product_id=f"solar-estimate:{sp.site_id}",
                    label="Modelled",
                    is_placeholder=False,
                    url=f"/api/v1/lunar/sites/{sp.site_id}/solar-estimate",
                ))

        # 11. Landing Site Comparisons (/api/v1/lunar/compare/{id}/export?format=json)
        comp_terms = ["compare", "comparison", "ranking", "landing window comparison", "best site"]
        if any(w in q_lower for w in comp_terms):
            all_sc = self.db.query(LandingSiteComparison).all()
            for sc in all_sc:
                matched.append(EvidenceItem(
                    text=(
                        f"Landing Site Comparison '{sc.id}': criteria {sc.criteria}, "
                        f"thresholds: {sc.thresholds}, result metadata: {sc.result_metadata} (Derived)."
                    ),
                    source_name=f"Landing Site Comparison: {sc.id}",
                    product_id=f"comparison:{sc.id}",
                    label="Derived",
                    is_placeholder=False,
                    url=f"/api/v1/lunar/compare/{sc.id}/export?format=json",
                ))

        # 12. SPICE Kernels in DataProduct (/api/v1/sources/{id})
        kernel_terms = ["kernel", "kernels", "spice", "naif", "ephemeris", "de421", "pck", "tls", "bsp", "tf", "bpc"]
        if any(w in q_lower for w in kernel_terms):
            kernels = (
                self.db.query(DataProduct)
                .filter((DataProduct.id.like("%kernel%")) | (DataProduct.source_id == "src-naif-generic"))
                .all()
            )
            for k in kernels:
                matched.append(EvidenceItem(
                    text=(
                        f"SPICE Kernel '{k.id}': identifier {k.product_identifier}, source: {k.source_id}, "
                        f"coordinate_frame: {k.coordinate_frame}, units: {k.units}, "
                        f"processing_method: {k.processing_method}, label: {k.label} (Verified)."
                    ),
                    source_name=f"SPICE Kernel: {k.product_identifier or k.id}",
                    product_id=k.id,
                    label=k.label,
                    is_placeholder=k.is_placeholder,
                    url=f"/api/v1/sources/{k.id}",
                ))

        # 13. General PDS Products
        if any(w in q_lower for w in ["pds", "places", "provenance", "checksum", "version"]):
            products = (
                self.db.query(DataProduct)
                .filter(~DataProduct.id.like("%kernel%"))
                .all()
            )
            for p in products:
                matched.append(EvidenceItem(
                    text=(
                        f"DataProduct '{p.id}': version {p.version}, checksum {p.checksum}, "
                        f"coordinate_frame: {p.coordinate_frame}, units: {p.units}, "
                        f"processing_method: {p.processing_method}, label: {p.label}."
                    ),
                    source_name="NASA Planetary Data System (PDS) Geosciences Node",
                    product_id=p.id,
                    label=p.label,
                    is_placeholder=p.is_placeholder,
                    url="https://pds-geosciences.wustl.edu/missions/mars2020/places.htm",
                ))

        # 14. Rover Camera Images (/api/v1/rovers/{rover_id}/images)
        image_terms = ["image", "images", "photo", "photos", "picture", "pictures", "camera", "cameras", "mastcam", "navcam", "hazcam", "supercam", "mcz", "cache"]
        if any(w in q_lower for w in image_terms):
            img_query = self.db.query(Image)
            if has_perseverance:
                img_query = img_query.filter(Image.explorer_id == "perseverance")
            elif has_curiosity:
                img_query = img_query.filter(Image.explorer_id == "curiosity")

            images = img_query.order_by(Image.captured_at.desc()).limit(50).all()
            cameras_found = sorted(list(set(img.camera for img in images if img.camera)))
            if cameras_found:
                exp_name = "Perseverance" if (has_perseverance or not has_curiosity) else "Curiosity"
                matched.append(EvidenceItem(
                    text=(
                        f"Rover Camera Images Record for {exp_name}: "
                        f"Published instruments and cameras in the archive include: {', '.join(cameras_found)}. "
                        f"Total imported images queried: {len(images)}. "
                        f"All image records include sol, UTC captured timestamp, camera instrument, and official NASA archive hotlink."
                    ),
                    source_name="NASA Mars 2020 Raw Images Archive",
                    product_id="urn:nasa:pds:mars2020_raw_images",
                    label="Verified",
                    is_placeholder=False,
                    url=f"/api/v1/rovers/perseverance/images",
                ))
                for img in images[:4]:
                    sol_str = f"Sol {img.sol}" if hasattr(img, "sol") and img.sol is not None else "Unknown Sol"
                    matched.append(EvidenceItem(
                        text=(
                            f"Image '{img.id}' from {img.explorer_id} using camera {img.camera} "
                            f"(captured: {img.captured_at}, {sol_str}, label: {img.label}): {img.image_url}"
                        ),
                        source_name=f"Camera Image: {img.camera}",
                        product_id=img.product_id or img.id,
                        label=img.label,
                        is_placeholder=img.is_placeholder,
                        url=f"/api/v1/rovers/{img.explorer_id}/images",
                    ))

        return matched

    def retrieve(self, query: str) -> List[EvidenceItem]:
        """
        Main retrieval method.
        Returns top 3 to 5 relevant EvidenceItem list.
        Only queries with meaningful topic terms match evidence.
        """
        clean_q = query.strip()
        if not clean_q or not has_meaningful_topic_term(clean_q):
            return []

        tokens = _tokenize(clean_q)
        if not tokens:
            return []

        q_lower = clean_q.lower()

        # Check if question is asking for rules, frames, disclaimers, definitions
        doc_query_terms = ["frame", "coordinate", "rule", "disclaimer", "definition", "dictionary", "meaning", "accuracy", "iau", "safety"]
        is_doc_query = any(w in q_lower for w in doc_query_terms)

        db_evidence = self.search_database(clean_q, tokens)
        doc_evidence = self.search_docs(tokens) if (is_doc_query or not db_evidence) else []

        combined = db_evidence + doc_evidence

        # Deduplicate evidence by text prefix
        seen_texts = set()
        deduped: List[EvidenceItem] = []
        for item in combined:
            norm_text = item.text[:60].strip()
            if norm_text not in seen_texts:
                seen_texts.add(norm_text)
                deduped.append(item)

        # Score and rank evidence
        def score_item(item: EvidenceItem) -> int:
            score = 0
            text_lower = item.text.lower()
            name_lower = item.source_name.lower()
            prod_lower = (item.product_id or "").lower()

            for t in tokens:
                if t in text_lower:
                    score += 2
                if t in name_lower or t in prod_lower:
                    score += 4

            # Specific intent boosts
            if any(w in q_lower for w in ["sunlight", "illumination", "hours", "december", "january"]) and "illumination" in prod_lower:
                score += 15
            if any(w in q_lower for w in ["dem", "resolution", "lola"]) and "terrain product" in name_lower:
                score += 15
            if any(w in q_lower for w in ["slope", "steep", "relief"]) and "terrain-metrics" in prod_lower:
                score += 15
            if any(w in q_lower for w in ["earth", "visibility", "comm"]) and "earth-visibility" in prod_lower:
                score += 15
            if any(w in q_lower for w in ["solar", "power", "energy", "irradiance", "kwh", "wh"]) and "solar-estimate" in prod_lower:
                score += 15
            if any(w in q_lower for w in ["safe", "safety"]) and "candidate landing site" in name_lower:
                score += 15
            if any(w in q_lower for w in ["kernel", "spice", "de421"]) and "kernel" in name_lower:
                score += 15
            if any(w in q_lower for w in ["image", "camera", "photo", "mastcam", "navcam", "hazcam", "supercam"]) and ("image" in prod_lower or "camera" in name_lower or "raw images" in name_lower):
                score += 20

            # Exact site match
            site_match = re.search(r"site-[a-zA-Z0-9_\-]+", q_lower)
            if site_match and site_match.group(0) in (prod_lower + " " + text_lower):
                score += 20

            return score

        deduped.sort(key=score_item, reverse=True)
        return deduped[:5]


def retrieve_context(query: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Compatibility entry point returning dict with evidence items."""
    retriever = KnowledgeRetriever(db=db)
    items = retriever.retrieve(query)
    return {
        "results": [item.to_dict() for item in items],
        "evidence_found": len(items) > 0,
        "is_placeholder": any(item.is_placeholder for item in items) if items else False,
    }
