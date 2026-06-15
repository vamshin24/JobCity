import { Suspense, useEffect, useState } from "react";
import JobsCityScene from "@/components/three/JobsCityScene";
import JobDetailPopup from "@/components/JobDetailPopup";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";

export default function JobsCityPage() {
  const [selected, setSelected] = useState(null); // {id (company_id), name, city, state, color, floors}
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!selected) return;
    setLoadingJobs(true);
    api
      .get("/jobs", {
        params: { company_id: selected.id, city: selected.city, state: selected.state, limit: 50 },
      })
      .then((r) => setJobs(r.data.items))
      .finally(() => setLoadingJobs(false));
  }, [selected]);

  return (
    <div className="fixed inset-0">
      <Suspense fallback={null}>
        <JobsCityScene onCompanyClick={setSelected} selected={selected} query={query} />
      </Suspense>

      {/* Floating search */}
      <div className="absolute top-20 left-4 z-20 pointer-events-auto">
        <div className="glass rounded-full p-1 flex items-center pl-4 w-[280px]">
          <Input
            data-testid="jobs-search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search city, company, role…"
            className="bg-transparent border-0 focus-visible:ring-0 text-white placeholder:text-white/40"
          />
        </div>
      </div>

      {/* Bottom legend */}
      <div className="absolute bottom-4 left-4 z-20 pointer-events-auto glass rounded-2xl px-4 py-3 max-w-sm">
        <div className="label-mono">JOBS CITY · GUIDE</div>
        <div className="text-sm text-white/70 mt-1">
          Each building is a company hiring in that city. Building height = number of open jobs.
          <span className="text-white/40"> Drag to orbit · scroll to zoom · click a tower.</span>
        </div>
      </div>

      <JobDetailPopup
        company={selected}
        jobs={jobs}
        loading={loadingJobs}
        query={query}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
