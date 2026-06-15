import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast, Toaster } from "sonner";

const TITLE_SUGGESTIONS = [
  "Software Engineer",
  "Frontend Engineer",
  "Backend Engineer",
  "Full Stack Engineer",
  "ML Engineer",
  "Data Scientist",
  "Robotics Engineer",
  "DevOps Engineer",
  "Mobile Engineer",
  "Product Designer",
];

export default function OnboardingPage() {
  const { user, applicant, refresh } = useAuth();
  const nav = useNavigate();

  const [title, setTitle] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState([]);
  const [resumeUrl, setResumeUrl] = useState("");
  const [experience, setExperience] = useState("entry");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user === false) nav("/login");
  }, [user, nav]);

  useEffect(() => {
    if (applicant) {
      setTitle(applicant.title || "");
      setSkills(applicant.skills || []);
      setResumeUrl(applicant.resume_url || "");
      setExperience(applicant.experience_level || "entry");
    }
  }, [applicant]);

  const addSkill = (raw) => {
    const s = raw.trim();
    if (!s) return;
    if (skills.includes(s)) return;
    if (skills.length >= 20) {
      toast.info("Max 20 skills.");
      return;
    }
    setSkills([...skills, s]);
  };

  const onSkillKey = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(skillInput);
      setSkillInput("");
    } else if (e.key === "Backspace" && !skillInput && skills.length) {
      setSkills(skills.slice(0, -1));
    }
  };

  const save = async (skip = false) => {
    setBusy(true);
    try {
      if (!skip) {
        await api.patch("/applicants/me", {
          title,
          skills,
          resume_url: resumeUrl,
          experience_level: experience,
        });
        toast.success("Profile saved · your tower is ready.");
        await refresh();
      }
      nav("/applicants-city");
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  if (!user) {
    return <div className="pt-32 text-center text-white/60 label-mono">LOADING…</div>;
  }

  return (
    <div className="min-h-screen pt-28 pb-20 px-4">
      <Toaster theme="dark" position="top-right" />
      <div className="max-w-2xl mx-auto">
        <div className="label-mono text-[#00FFCC]">STEP 2 OF 2 · OPTIONAL</div>
        <h1 className="text-3xl sm:text-4xl font-black mt-1">
          Polish your tower
        </h1>
        <p className="text-white/60 mt-2">
          None of this is required — fill what you want, skip the rest. You can edit later from your profile.
        </p>

        <form
          data-testid="onboarding-form"
          onSubmit={(e) => {
            e.preventDefault();
            save(false);
          }}
          className="mt-8 glass rounded-3xl p-7 space-y-6"
        >
          {/* Title */}
          <div>
            <Label className="label-mono text-white/50">TITLE</Label>
            <Input
              data-testid="onboarding-title-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Software Engineer"
              className="mt-1 bg-black/40 border-white/10 text-white"
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {TITLE_SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  data-testid={`title-suggest-${s.replace(/\s+/g, "-").toLowerCase()}`}
                  onClick={() => setTitle(s)}
                  className="px-2.5 py-1 rounded-full text-[11px] font-mono bg-white/5 hover:bg-white/10 text-white/60 border border-white/10"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Experience level */}
          <div>
            <Label className="label-mono text-white/50">EXPERIENCE</Label>
            <div className="mt-2 flex gap-2">
              {[
                { v: "entry", label: "ENTRY" },
                { v: "mid", label: "MID" },
                { v: "senior", label: "SENIOR" },
              ].map((opt) => (
                <button
                  key={opt.v}
                  type="button"
                  data-testid={`exp-${opt.v}-btn`}
                  onClick={() => setExperience(opt.v)}
                  className={`px-4 py-2 rounded-full text-xs font-mono tracking-widest border transition ${
                    experience === opt.v
                      ? "bg-[#00FFCC] text-black border-[#00FFCC]"
                      : "bg-transparent border-white/15 text-white/70 hover:bg-white/5"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div>
            <Label className="label-mono text-white/50">SKILLS</Label>
            <div className="mt-1 bg-black/40 border border-white/10 rounded-md px-2 py-1.5 min-h-[44px] flex flex-wrap gap-1.5 items-center">
              {skills.map((s) => (
                <span
                  key={s}
                  data-testid={`skill-chip-${s.replace(/\s+/g, "-").toLowerCase()}`}
                  className="px-2.5 py-1 rounded-full text-xs font-mono bg-[#00FFCC]/15 text-[#00FFCC] border border-[#00FFCC]/30 flex items-center gap-1.5"
                >
                  {s}
                  <button
                    type="button"
                    onClick={() => setSkills(skills.filter((x) => x !== s))}
                    className="text-[#00FFCC]/70 hover:text-white"
                    aria-label={`Remove ${s}`}
                  >
                    ×
                  </button>
                </span>
              ))}
              <input
                data-testid="onboarding-skill-input"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={onSkillKey}
                onBlur={() => {
                  addSkill(skillInput);
                  setSkillInput("");
                }}
                placeholder={skills.length ? "" : "React, FastAPI, ML… (Enter to add)"}
                className="flex-1 min-w-[140px] bg-transparent outline-none text-white text-sm placeholder:text-white/30 py-1"
              />
            </div>
            <div className="mt-1 text-[11px] text-white/40 font-mono">
              Press Enter or comma to add. Backspace to remove last.
            </div>
          </div>

          {/* Resume URL */}
          <div>
            <Label className="label-mono text-white/50">RESUME LINK</Label>
            <Input
              data-testid="onboarding-resume-input"
              value={resumeUrl}
              onChange={(e) => setResumeUrl(e.target.value)}
              placeholder="https:// · Google Drive, Notion, personal site…"
              className="mt-1 bg-black/40 border-white/10 text-white"
            />
            <div className="mt-1 text-[11px] text-white/40 font-mono">
              Anyone viewing your tower can open this link to see your resume.
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-2">
            <Button
              data-testid="onboarding-save-btn"
              type="submit"
              disabled={busy}
              className="btn-applicants rounded-full px-6 py-5 h-auto"
            >
              {busy ? "Saving…" : "Save & enter the city →"}
            </Button>
            <Button
              data-testid="onboarding-skip-btn"
              type="button"
              variant="ghost"
              onClick={() => save(true)}
              disabled={busy}
              className="text-white/60 rounded-full"
            >
              Skip for now
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
