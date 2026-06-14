import { useCallback, useEffect, useState } from "react";
import { api, ReviewItem } from "../api";

export default function TAReview() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [index, setIndex] = useState(0);
  const [stats, setStats] = useState({ pending: 0, approved: 0, overridden: 0, plagiarism_flags: 0 });
  const [overrideScore, setOverrideScore] = useState("");
  const [message, setMessage] = useState("");

  const current = queue[index];

  const refresh = useCallback(async () => {
    const [items, s] = await Promise.all([api.reviewQueue("pending"), api.reviewStats()]);
    setQueue(items);
    setStats(s);
    setIndex(0);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function approve() {
    if (!current) return;
    await api.reviewAction(current.grade_id, "approve");
    setMessage(`Approved ${current.student_id} — ${current.question_id}`);
    await refresh();
  }

  async function override() {
    if (!current) return;
    const score = parseFloat(overrideScore);
    if (Number.isNaN(score)) {
      setMessage("Enter a valid override score");
      return;
    }
    await api.reviewAction(current.grade_id, "override", score, "TA manual override");
    setMessage(`Overridden ${current.student_id} to ${score}`);
    setOverrideScore("");
    await refresh();
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key.toLowerCase() === "a") {
        e.preventDefault();
        approve();
      }
      if (e.key.toLowerCase() === "o") {
        e.preventDefault();
        document.getElementById("override-input")?.focus();
      }
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, queue.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          ["Pending", stats.pending],
          ["Approved", stats.approved],
          ["Overridden", stats.overridden],
          ["Plagiarism Flags", stats.plagiarism_flags],
        ].map(([label, val]) => (
          <div key={label as string} className="bg-white rounded-xl shadow p-4">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="text-2xl font-semibold">{val as number}</p>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm">
        Keyboard shortcuts: <kbd className="px-1 bg-white border rounded">A</kbd> Approve ·{" "}
        <kbd className="px-1 bg-white border rounded">O</kbd> Focus override ·{" "}
        <kbd className="px-1 bg-white border rounded">←</kbd>
        <kbd className="px-1 bg-white border rounded">→</kbd> Navigate
      </div>

      {message && <p className="text-sm text-emerald-700">{message}</p>}

      {!current ? (
        <div className="bg-white rounded-xl shadow p-8 text-center text-slate-500">No pending reviews 🎉</div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-4">
          <section className="bg-white rounded-xl shadow p-5 space-y-3">
            <div className="flex justify-between text-sm text-slate-500">
              <span>{current.exam_title}</span>
              <span>
                {index + 1}/{queue.length}
              </span>
            </div>
            <h2 className="text-xl font-semibold">
              {current.student_id} · {current.question_id}
            </h2>
            <div className="bg-slate-50 border rounded-lg p-4 min-h-[220px] whitespace-pre-wrap text-sm">
              {current.transcription || "(No transcription)"}
            </div>
            {current.plagiarism_flags.length > 0 && (
              <div className="border border-red-200 bg-red-50 rounded-lg p-3 text-sm text-red-800">
                ⚠ Plagiarism flagged ({current.plagiarism_flags.length}) — similarity up to{" "}
                {Math.max(...current.plagiarism_flags.map((f) => f.similarity_score)).toFixed(2)}
              </div>
            )}
          </section>

          <section className="bg-white rounded-xl shadow p-5 space-y-4">
            <div>
              <p className="text-sm text-slate-500">AI Proposed Grade</p>
              <p className="text-3xl font-bold text-brand-700">
                {current.grade.ai_score}/{current.grade.ai_max_score}
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-4 text-sm">{current.grade.ai_justification}</div>
            <div className="flex gap-3">
              <button onClick={approve} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded-lg font-medium">
                Approve (A)
              </button>
            </div>
            <div className="flex gap-2">
              <input
                id="override-input"
                className="border rounded-lg px-3 py-2 flex-1"
                placeholder="Override score"
                value={overrideScore}
                onChange={(e) => setOverrideScore(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && override()}
              />
              <button onClick={override} className="bg-orange-600 hover:bg-orange-700 text-white px-4 rounded-lg">
                Override
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
