import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import ApplicantsCityScene from "@/components/three/ApplicantsCityScene";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";
import { APPLICANT_CITY_COLORS } from "@/lib/colors";
import { toast } from "sonner";

const SPACING = 2.4;

export default function ApplicantsCityPage() {
  const { applicant: meApplicant } = useAuth();
  const nav = useNavigate();

  const [applicants, setApplicants] = useState([]);
  const [focus, setFocus] = useState(null); // applicant in side panel
  const [compareIds, setCompareIds] = useState([]);
  const [query, setQuery] = useState("");
  const [flyTarget, setFlyTarget] = useState(null);

  const handleApplicantsLoaded = useCallback((list) => setApplicants(list), []);

  const onBuildingClick = (a) => {
    setFocus(a);
  };

  const addToCompare = (a) => {
    setCompareIds((prev) => {
      if (prev.includes(a.id)) {
        toast.info("Already in compare set.");
        return prev;
      }
      if (prev.length >= 4) {
        toast.info("Compare set is full (max 4). Remove one first.");
        return prev;
      }
      toast.success(`${a.display_name} added to compare (${prev.length + 1}/4).`);
      return [...prev, a.id];
    });
  };

  const removeFromCompare = (id) =>
    setCompareIds((prev) => prev.filter((x) => x !== id));

  const myBuilding = useMemo(() => {
    if (!meApplicant) return null;
    return applicants.find((a) => a.id === meApplicant.applicant_id);
  }, [applicants, meApplicant]);

  const navigateToMe = () => {
    if (!myBuilding) {
      toast.error("Couldn't find your tower yet.");
      return;
    }
    setFlyTarget([myBuilding.grid_x * SPACING, myBuilding.grid_z * SPACING, Date.now()]);
    setFocus(myBuilding);
    toast("Flying to your tower…", { duration: 1500 });
  };

  // Build a quick lookup for the compare dock
  const idToApplicant = useMemo(() => {
    const m = new Map();
    applicants.forEach((a) => m.set(a.id, a));
    return m;
  }, [applicants]);

  return (
    <div className="fixed inset-0">
      <Suspense fallback={null}>
        <ApplicantsCityScene
          onApplicantClick={onBuildingClick}
          selectedIds={compareIds}
          focusId={focus?.id}
          flyTarget={flyTarget}
          query={query}
          onApplicantsLoaded={handleApplicantsLoaded}
        />
      </Suspense>

      {/* Floating search */}
      <div className="absolute top-20 left-4 z-20 pointer-events-auto">
        <div className="glass rounded-full p-1 flex items-center pl-4 w-[320px]">
          <Input
            data-testid="applicants-search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search name, title, level, github…"
            className="bg-transparent border-0 focus-visible:ring-0 text-white placeholder:text-white/40"
          />
        </div>
      </div>

      {/* Navigate-me button */}
      {meApplicant && (
        <div className="absolute top-20 right-4 z-20 pointer-events-auto">
          <Button
            data-testid="navigate-to-my-building-btn"
            onClick={navigateToMe}
            className="rounded-full bg-[#5BE3A3] text-black hover:bg-[#5BE3A3]/90 font-semibold shadow-lg shadow-[#5BE3A3]/20"
          >
            ↗ Navigate to my tower
          </Button>
        </div>
      )}

      {/* Top guide */}
      <div className="absolute top-36 left-4 z-20 pointer-events-auto glass rounded-2xl px-4 py-3 max-w-md">
        <div className="label-mono text-[#5BE3A3]">APPLICANTS CITY · GUIDE</div>
        <div className="text-sm text-white/70 mt-1">
          Each tower is an applicant. Floors = job applications. Tap a tower to inspect.
          Use “+ Add to compare” on up to 4 towers to compare side-by-side.
        </div>
      </div>

      {/* Compare dock */}
      {compareIds.length > 0 && (
        <div
          data-testid="compare-bar"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 pointer-events-auto glass-strong rounded-3xl px-4 py-3 flex items-center gap-3 flex-wrap max-w-[92vw]"
        >
          <div className="label-mono text-[#5BE3A3]">COMPARE {compareIds.length}/4</div>
          <div className="flex items-center gap-2">
            {compareIds.map((id) => {
              const a = idToApplicant.get(id);
              if (!a) return null;
              const c = APPLICANT_CITY_COLORS[a.experience_level] || APPLICANT_CITY_COLORS.entry;
              return (
                <span
                  key={id}
                  data-testid={`compare-chip-${id}`}
                  className="pl-2 pr-1 py-1 rounded-full flex items-center gap-1.5 bg-black/40 border border-white/10 text-xs font-mono"
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: c, boxShadow: `0 0 6px ${c}` }}
                  />
                  {a.display_name}
                  <button
                    onClick={() => removeFromCompare(id)}
                    className="ml-1 w-5 h-5 rounded-full bg-white/5 hover:bg-white/15 text-white/70 leading-none"
                    aria-label="Remove from compare"
                    data-testid={`compare-remove-${id}`}
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
          <Button
            data-testid="compare-go-btn"
            disabled={compareIds.length < 2}
            onClick={() => nav(`/compare?ids=${compareIds.join(",")}`)}
            className="btn-applicants rounded-full"
            size="sm"
          >
            Compare side-by-side →
          </Button>
          <Button
            data-testid="compare-clear-btn"
            variant="ghost"
            size="sm"
            onClick={() => setCompareIds([])}
            className="text-white/60"
          >
            Clear
          </Button>
        </div>
      )}

      {/* Side panel (Sheet) */}
      <ApplicantSidePanel
        applicant={focus}
        onClose={() => setFocus(null)}
        onAddCompare={() => focus && addToCompare(focus)}
        inCompareSet={focus ? compareIds.includes(focus.id) : false}
        compareFull={compareIds.length >= 4}
      />
    </div>
  );
}

function ApplicantSidePanel({ applicant, onClose, onAddCompare, inCompareSet, compareFull }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!applicant) return;
    setDetail(null);
    setLoading(true);
    import("@/lib/api").then(({ api }) =>
      api
        .get(`/applicants/${applicant.id}`)
        .then((r) => setDetail(r.data.applicant))
        .catch(() => setDetail(null))
        .finally(() => setLoading(false))
    );
  }, [applicant]);

  if (!applicant) return null;

  const color = APPLICANT_CITY_COLORS[applicant.experience_level] || APPLICANT_CITY_COLORS.entry;
  const skills = detail?.skills || [];
  const resumeUrl = detail?.resume_url || "";
  const title = detail?.title || applicant.title || "";

  return (
    <Sheet open={!!applicant} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        data-testid="applicant-side-panel"
        side="right"
        className="bg-[#06120b]/95 backdrop-blur-2xl border-l border-[#5BE3A3]/15 text-white w-full sm:max-w-md"
      >
        <SheetHeader className="pb-2">
          <div className="flex items-center gap-3">
            <div
              className="w-14 h-14 rounded-xl flex items-center justify-center font-[Unbounded] text-2xl font-black"
              style={{
                background: color,
                color: "#0b1a10",
                boxShadow: `0 0 24px ${color}55`,
              }}
              data-testid="applicant-avatar-block"
            >
              {applicant.display_name?.[0] || "?"}
            </div>
            <div className="flex-1 text-left">
              <div className="label-mono" style={{ color }}>
                {applicant.experience_level.toUpperCase()}
                {title && ` · ${title.toUpperCase()}`}
              </div>
              <SheetTitle
                className="font-[Unbounded] text-2xl font-black text-white text-left"
                data-testid="applicant-name"
              >
                {applicant.display_name}
              </SheetTitle>
            </div>
          </div>
        </SheetHeader>

        {/* Stats row */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="glass rounded-2xl p-4">
            <div className="label-mono text-white/50">APPLICATIONS</div>
            <div
              className="font-mono text-3xl font-bold mt-1"
              style={{ color: "#5BE3A3" }}
              data-testid="applicant-applications-count"
            >
              {applicant.floors}
            </div>
          </div>
          <div className="glass rounded-2xl p-4">
            <div className="label-mono text-white/50">GITHUB</div>
            <div className="font-mono text-base font-semibold mt-1 text-white truncate">
              {applicant.has_github ? `${applicant.github_commits_30d} / 30d` : "—"}
            </div>
          </div>
        </div>

        {/* Skills */}
        <div className="mt-4">
          <div className="label-mono text-white/50">SKILLS</div>
          {loading && (
            <div className="mt-2 flex flex-wrap gap-2">
              <div className="h-6 w-16 bg-white/5 rounded-full animate-pulse" />
              <div className="h-6 w-20 bg-white/5 rounded-full animate-pulse" />
              <div className="h-6 w-12 bg-white/5 rounded-full animate-pulse" />
            </div>
          )}
          {!loading && skills.length === 0 && (
            <div className="mt-1 text-white/40 text-sm">— not provided</div>
          )}
          {!loading && skills.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2" data-testid="applicant-skills-list">
              {skills.map((s) => (
                <span
                  key={s}
                  className="px-3 py-1 rounded-full text-xs font-mono bg-[#5BE3A3]/10 text-[#5BE3A3] border border-[#5BE3A3]/30"
                >
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Resume */}
        <div className="mt-4">
          <div className="label-mono text-white/50">RESUME</div>
          {resumeUrl ? (
            <a
              data-testid="applicant-resume-link"
              href={resumeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#5BE3A3]/10 text-[#5BE3A3] border border-[#5BE3A3]/30 hover:bg-[#5BE3A3]/20 transition text-sm font-mono"
            >
              View resume ↗
            </a>
          ) : (
            <div className="mt-1 text-white/40 text-sm">— not provided</div>
          )}
        </div>

        {/* Compare action */}
        <div className="mt-6 pt-4 border-t border-white/5">
          <Button
            data-testid="add-to-compare-btn"
            onClick={onAddCompare}
            disabled={inCompareSet || compareFull}
            className="w-full rounded-full bg-[#5BE3A3] text-black hover:bg-[#5BE3A3]/90 disabled:bg-white/10 disabled:text-white/40"
          >
            {inCompareSet
              ? "Already in compare"
              : compareFull
              ? "Compare set full (4/4)"
              : "+ Add to compare"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
